from __future__ import annotations

from collections import Counter
from math import log, sqrt
from random import randint
from typing import TYPE_CHECKING, Any, Sequence
from uuid import UUID, uuid7

import rjieba
from advanced_alchemy.filters import CollectionFilter
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService, schema_dump
from advanced_alchemy.service.typing import ModelDictT
from selectolax.parser import HTMLParser

from application.mixins import PaginationServiceMixin
from application.permalink import build_permalink
from application.sanitizer import sanitize_html
from application.taxonomies.services import (
    CategoryRepository,
    FeatureRepository,
    SpecialRepository,
    TagService,
)

from .models import Article

if TYPE_CHECKING:
    from application.accounts.models import User

# 中文句子分隔符（句末 + 换行）
_SENTENCE_SPLITS = "。！？!?\n"
_STOPWORDS = {
    "我们",
    "你们",
    "他们",
    "以及",
    "其中",
    "这个",
    "那个",
    "进行",
    "相关",
    "通过",
}


def _split_sentences(text: str) -> list[str]:
    """按中英文标点切分句子"""
    sentences: list[str] = []
    buf: list[str] = []
    for ch in text:
        buf.append(ch)
        if ch in _SENTENCE_SPLITS:
            s = "".join(buf).strip()
            if s:
                sentences.append(s)
            buf = []
    tail = "".join(buf).strip()
    if tail:
        sentences.append(tail)
    return sentences


def _truncate_at_boundary(text: str, max_chars: int) -> str:
    """截断到 max_chars 内最近的标点，避免半截词。"""
    cut = text[:max_chars]
    # 1. 优先找句末标点（。？！）- 落在完整句子
    for i in range(len(cut) - 1, -1, -1):
        if cut[i] in "。?!":
            return cut[: i + 1]
    # 2. 其次找句中标点（，、；,）- 截到标点前
    for i in range(len(cut) - 1, -1, -1):
        if cut[i] in "，、;,":
            truncated = cut[:i].rstrip()
            if truncated:
                return truncated
    # 3. 都找不到或截断后为空 - 硬切
    return cut.rstrip()


def _tokenize_sentence(sentence: str) -> list[str]:
    return [
        t
        for w in rjieba.cut(sentence)
        if (t := w.strip()) and len(t) > 1 and t not in _STOPWORDS
    ]


def _idf(tokenized: list[list[str]]) -> dict[str, float]:
    """平滑 IDF"""
    n = len(tokenized)
    df: Counter[str] = Counter()
    for ts in tokenized:
        for t in set(ts):
            df[t] += 1
    return {t: log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}


def _tfidf_vec(tokens: list[str], idf_map: dict[str, float]) -> dict[str, float]:
    """稀疏 TF-IDF 向量 + L2 归一"""
    tf = Counter(tokens)
    vec = {t: c * idf_map.get(t, 1.0) for t, c in tf.items()}
    norm = sqrt(sum(v * v for v in vec.values())) or 1.0
    return {t: v / norm for t, v in vec.items()}


def _cosine_sparse(a: dict[str, float], b: dict[str, float]) -> float:
    """稀疏向量余弦（两向量已归一）"""
    if len(a) > len(b):
        a, b = b, a
    return sum(v * b.get(k, 0.0) for k, v in a.items())


def _build_similarity_matrix(vecs: list[dict[str, float]]) -> list[list[float]]:
    n = len(vecs)
    m = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            s = _cosine_sparse(vecs[i], vecs[j])
            # 过滤极小噪声边
            if s > 1e-6:
                m[i][j] = s
                m[j][i] = s
    return m


def _pagerank(
    sim: list[list[float]],
    alpha: float = 0.85,
    max_iter: int = 60,
    tol: float = 1e-6,
) -> list[float]:
    """纯 Python PageRank"""
    n = len(sim)
    if n == 0:
        return []

    ranks = [1.0 / n] * n
    out_sum = [sum(row) for row in sim]

    for _ in range(max_iter):
        new_ranks = [(1.0 - alpha) / n] * n

        for j in range(n):
            if out_sum[j] == 0.0:
                # dangling node 均匀分发
                share = alpha * ranks[j] / n
                for i in range(n):
                    new_ranks[i] += share
            else:
                share_base = alpha * ranks[j] / out_sum[j]
                row = sim[j]
                for i in range(n):
                    w = row[i]
                    if w > 0:
                        new_ranks[i] += share_base * w

        delta = sum(abs(new_ranks[i] - ranks[i]) for i in range(n))
        ranks = new_ranks
        if delta < tol:
            break

    return ranks


def extract_description_textrank(
    html_text: str,
    sentences_count: int = 2,
    max_chars: int = 150,
) -> str:
    """
    使用纯 Python TextRank 生成摘要（不依赖 sklearn/scipy/networkx）。
    失败自动降级为纯文本截取。
    """
    if not html_text or not html_text.strip():
        return ""

    # 1. selectolax 提取纯文本
    tree = HTMLParser(html_text)
    plain_text = (
        tree.body.text(separator="\n") if tree.body else tree.text(separator="\n")
    ).strip()

    if not plain_text:
        return ""
    if len(plain_text) <= max_chars:
        return plain_text

    # 2. 切句
    sentences = _split_sentences(plain_text)
    if not sentences:
        return _truncate_at_boundary(plain_text, max_chars)

    if len(sentences) <= sentences_count:
        result = "".join(sentences)
        return (
            _truncate_at_boundary(result, max_chars)
            if len(result) > max_chars
            else result
        )

    try:
        # 3. 分词 + TF-IDF 稀疏向量
        tokenized = [_tokenize_sentence(s) for s in sentences]
        idf_map = _idf(tokenized)
        vecs = [_tfidf_vec(ts, idf_map) for ts in tokenized]

        # 4. 相似图 + TextRank(PageRank)
        sim = _build_similarity_matrix(vecs)
        scores = _pagerank(sim, alpha=0.85, max_iter=60, tol=1e-6)

        # 5. 取 top N，保持原文顺序
        ranked_idx = sorted(
            range(len(sentences)), key=lambda i: scores[i], reverse=True
        )
        top_idx = sorted(ranked_idx[:sentences_count])
        result = "".join(sentences[i] for i in top_idx)

        # 6. 截断保护
        if len(result) > max_chars:
            result = _truncate_at_boundary(result, max_chars)

        return result or _truncate_at_boundary(plain_text, max_chars)

    except Exception:
        # 任何异常全部降级
        return _truncate_at_boundary(plain_text, max_chars)


def extract_cover_url(html_text: str) -> str:
    """从 HTML 提取第一张图片的 src 作为封面（使用 selectolax）。"""
    if not html_text or not html_text.strip():
        return ""

    tree = HTMLParser(html_text)
    img_node = tree.css_first("img")
    if not img_node:
        return ""

    src = img_node.attributes.get("src", "")
    return src if isinstance(src, str) else ""


class ArticleRepository(SQLAlchemyAsyncRepository[Article]):
    model_type = Article


class ArticleService(
    PaginationServiceMixin,
    SQLAlchemyAsyncRepositoryService[Article],
):
    repository_type = ArticleRepository

    async def create_many_for_categories(
        self,
        data: ModelDictT[Article],
        creator: User,
    ) -> Sequence[Article]:
        if not isinstance(data, dict):
            data = schema_dump(data)

        categories = await CategoryRepository(session=self.repository.session).get_many(
            CollectionFilter(field_name="id", values=data.pop("categories"))
        )

        datas = [
            {
                **data,
                "category": category,
                "creator": creator,
                "views": randint(10000, 99999),
            }
            for category in categories
        ]
        return await super().create_many(datas)

    async def to_model_on_create(
        self, data: ModelDictT[Article]
    ) -> ModelDictT[Article]:
        if not isinstance(data, dict):
            data = schema_dump(data)

        tag_names = data.pop("tags", None)
        special_ids = data.pop("specials", None)
        feature_ids = data.pop("features", None)
        # build_permalink 需要 model.id, 与 CategoryService 一致: 显式生成
        data["id"] = uuid7()
        model = await super().to_model(data)

        # 净化 HTML
        model.text = sanitize_html(data.get("text", ""))

        # 描述为空时自动提取摘要
        if not model.description:
            model.description = extract_description_textrank(model.text)

        # 封面为空时自动提取正文第一张图
        if not model.cover_url:
            model.cover_url = extract_cover_url(model.text)

        model.path = build_permalink(model.category.content_path, model)

        if special_ids:
            special_repo = SpecialRepository(session=self.repository.session)
            model.specials = await special_repo.get_many(
                CollectionFilter(field_name="id", values=special_ids)
            )

        if feature_ids:
            feature_repo = FeatureRepository(session=self.repository.session)
            model.features = await feature_repo.get_many(
                CollectionFilter(field_name="id", values=feature_ids)
            )

        if tag_names:
            tag_service = TagService(session=self.repository.session)
            model.tags = await tag_service.resolve_tags(tag_names)

        return model

    async def to_model_on_update(
        self, data: ModelDictT[Article]
    ) -> ModelDictT[Article]:
        if not isinstance(data, dict):
            data = schema_dump(data)

        tag_names = data.pop("tags", None)
        special_updated_ids = data.pop("specials", None)
        feature_updated_ids = data.pop("features", None)

        category_id = data.pop("category", None)
        if category_id:
            data["category_id"] = UUID(category_id)

        data = await super().to_model(data)

        # 净化 HTML
        data.text = sanitize_html(data.text or "")

        # 描述为空时自动提取摘要
        if not data.description:
            data.description = extract_description_textrank(data.text)

        if not data.cover_url:
            data.cover_url = extract_cover_url(data.text)

        if feature_updated_ids is not None:
            feature_repo = FeatureRepository(session=self.repository.session)
            data.features = await feature_repo.get_many(
                CollectionFilter(field_name="id", values=feature_updated_ids)
            )

        if special_updated_ids is not None:
            special_repo = SpecialRepository(session=self.repository.session)
            data.specials = await special_repo.get_many(
                CollectionFilter(field_name="id", values=special_updated_ids)
            )

        if tag_names is not None:
            tag_service = TagService(session=self.repository.session)
            data.tags = await tag_service.resolve_tags(tag_names)

        return data

    async def update(
        self, data: ModelDictT[Article], item_id: Any | None = None, **kwargs
    ) -> Article:
        history = await self.repository.get(item_id)
        old_category_id = history.category_id

        model = await super().update(data, item_id, **kwargs)

        if model.category_id != old_category_id:
            # repository.update 内部 merge(load=False) 会过期已加载的关系,
            # 必须重新取新分类; 顺带修复: 原逻辑用的是旧分类的模板/旧 {category}
            model.category = await CategoryRepository(
                session=self.repository.session
            ).get(model.category_id)
            model.path = build_permalink(model.category.content_path, model)

        return model
