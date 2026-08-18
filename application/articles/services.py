from __future__ import annotations

from random import randint
from typing import TYPE_CHECKING, Any, Sequence
from uuid import UUID, uuid7

import rjieba
from advanced_alchemy.filters import CollectionFilter
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService, schema_dump
from advanced_alchemy.service.typing import ModelDictT
from scipy.sparse import csr_matrix
from selectolax.parser import HTMLParser
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

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


def extract_description_textrank(
    html_text: str,
    sentences_count: int = 2,
    max_chars: int = 150,
) -> str:
    """
    使用 TextRank（无 TF‑IDF）生成摘要。
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
        return plain_text[:max_chars]
    if len(sentences) <= sentences_count:
        result = "".join(sentences)
        return (
            _truncate_at_boundary(result, max_chars)
            if len(result) > max_chars
            else result
        )

    try:
        # 3. rjieba 分词
        tokenized: list[list[str]] = [
            [w for w in rjieba.cut(s) if len(w) > 1] for s in sentences
        ]

        # 4. 构建词频矩阵（BM25 风格，不依赖 TF‑IDF）
        vocab: dict[str, int] = {}
        rows, cols, data = [], [], []

        for i, words in enumerate(tokenized):
            seen = set()
            for w in words:
                if w not in vocab:
                    vocab[w] = len(vocab)
                idx = vocab[w]
                if idx not in seen:
                    rows.append(i)
                    cols.append(idx)
                    data.append(1.0)
                    seen.add(idx)

        X = csr_matrix((data, (rows, cols)), shape=(len(sentences), len(vocab)))
        X = normalize(X, norm="l2", axis=1)

        # 5. 句子相似度矩阵（余弦）
        sim = cosine_similarity(X, dense_output=False)

        # 6. TextRank（PageRank on similarity graph）
        import networkx as nx

        graph = nx.from_scipy_sparse_array(sim)
        scores = nx.pagerank(graph, alpha=0.85, max_iter=100)

        # 7. 取 top N 句，保持原文顺序
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_indices = sorted(i for i, _ in ranked[:sentences_count])
        result = "".join(sentences[i] for i in top_indices)

        # 8. 截断保护
        if len(result) > max_chars:
            result = _truncate_at_boundary(result, max_chars)

        return result or plain_text[:max_chars]

    except Exception:
        # 任何异常（NetworkX / 稀疏矩阵 / 迭代不收敛）全部降级
        return plain_text[:max_chars]


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
