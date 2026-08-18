from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any, Generic
from uuid import UUID, uuid7

from advanced_alchemy.exceptions import RepositoryError
from advanced_alchemy.filters import CollectionFilter
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.repository.typing import ModelT
from advanced_alchemy.service import (
    SQLAlchemyAsyncRepositoryService,
    is_dict,
    schema_dump,
)
from advanced_alchemy.service.typing import ModelDictT
from fastnanoid import generate
from litestar.exceptions import ClientException
from litestar.status_codes import HTTP_409_CONFLICT
from litestar.utils.path import normalize_path
from pypinyin import Style, lazy_pinyin
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from application.checks import check_path_unique
from application.contents.models import Content
from application.contents.services import ContentRepository
from application.mixins import PaginationServiceMixin
from application.permalink import build_permalink

from .models import Category, Feature, Special, Tag

# ---------- Tag slug 生成 ----------
_SLUG_KEEP = re.compile(r"[^a-z0-9-]+")


def _make_tag_slug(name: str, existing_slugs: set[str]) -> str:
    """
    把 Tag 名字转为 URL slug。

    规则:
        1. 中文转拼音（无声调）
        2. 英文小写保留
        3. 标点/空格转连字符
        4. 处理后为空（全特殊符号如 C++/C#/.NET）-> t-{nanoid}
        5. 拼音冲突 -> changcheng / changcheng2 / changcheng3
    """
    if not name or not name.strip():
        return f"t-{generate(size=10)}"

    parts = lazy_pinyin(name.strip(), style=Style.NORMAL)
    joined = "".join(parts).lower()

    slug = _SLUG_KEEP.sub("-", joined).strip("-")
    slug = re.sub(r"-+", "-", slug)

    if not slug:
        return f"t-{generate(size=10)}"

    if slug in existing_slugs:
        base = slug
        n = 2
        while f"{base}{n}" in existing_slugs:
            n += 1
        slug = f"{base}{n}"

    return slug


# ---------- Feature slug 生成 ----------


def _make_feature_slug(name: str, existing_slugs: set[str]) -> str:
    """把 Feature 名字转为 slug (规则同 _make_tag_slug, 前缀 f-)。"""
    if not name or not name.strip():
        return f"f-{generate(size=10)}"

    parts = lazy_pinyin(name.strip(), style=Style.NORMAL)
    joined = "".join(parts).lower()

    slug = _SLUG_KEEP.sub("-", joined).strip("-")
    slug = re.sub(r"-+", "-", slug)

    if not slug:
        return f"f-{generate(size=10)}"

    if slug in existing_slugs:
        base = slug
        n = 2
        while f"{base}{n}" in existing_slugs:
            n += 1
        slug = f"{base}{n}"

    return slug


class CategoryRepository(SQLAlchemyAsyncRepository[Category]):
    model_type = Category


class TagRepository(SQLAlchemyAsyncRepository[Tag]):
    model_type = Tag


class SpecialRepository(SQLAlchemyAsyncRepository[Special]):
    model_type = Special


class FeatureRepository(SQLAlchemyAsyncRepository[Feature]):
    model_type = Feature


type CategoryTree = list[dict[str, Any]]


class CategoryService(
    PaginationServiceMixin, SQLAlchemyAsyncRepositoryService[Category]
):
    repository_type = CategoryRepository
    loader_options = [Category.parent]

    @staticmethod
    def build_tree(
        categories: Sequence[Category],
        root_id: UUID | None = None,
    ) -> CategoryTree:

        if not categories:
            return []

        nodes = [{**cat.to_dict(), "children": []} for cat in categories]
        node_dict = {node["id"]: node for node in nodes}
        tree: CategoryTree = []

        for node in nodes:
            if node["parent_id"] and node["parent_id"] in node_dict:
                node_dict[node["parent_id"]]["children"].append(node)
            else:
                tree.append(node)

        if root_id is not None:
            return [node_dict[root_id]] if root_id in node_dict else []

        return tree

    async def get_tree(self, root_id: UUID | None = None):
        return self.build_tree(
            await self.get_many(order_by=[("priority", True)]), root_id
        )

    async def get_root_categories(self) -> Sequence[Category]:
        return await self.get_many(order_by=[("priority", True)], parent_id=None)

    async def delete(self, item_id: Any, **kwargs: Any) -> None:
        await ContentRepository(session=self.repository.session).delete_where(
            Content.category_id == item_id,
        )
        await super().delete(item_id, **kwargs)

    async def to_model_on_create(
        self, data: ModelDictT[Category]
    ) -> ModelDictT[Category]:
        model = await super().to_model(
            {
                "id": uuid7(),
                **schema_dump(data),
            }
        )
        if model.parent_id:
            model.parent = await self.repository.get(model.parent_id)
            model.trail = f"{model.parent.trail}.{model.id}"
        else:
            model.trail = str(model.id)

        model.path = normalize_path(self._generate_path(model))
        model.content_path = normalize_path(model.content_path)
        await check_path_unique(self.repository.session, model.path)
        return model

    async def update(
        self, data: ModelDictT[Category], item_id: Any | None = None, **kwargs
    ) -> Category:
        model = await super().to_model(data, "update")
        pk_value = item_id or self.repository.get_id_attribute_value(
            data, id_attribute=kwargs.get("id_attribute")
        )
        if pk_value is None:
            raise RepositoryError("Could not identify ID attribute value")

        history = await self.repository.get(pk_value, with_for_update=True)
        old_parent_id, old_trail, old_path = (
            history.parent_id,
            history.trail,
            history.path,
        )

        try:
            # ① 移动校验（写入前, 异常零副作用）
            new_parent = await self._resolve_parent(model.parent_id, history)

            updated = await super().update(model, pk_value, **kwargs)

            # ② 父变 → 重算自身 trail → 级联子孙
            if old_parent_id != updated.parent_id:
                updated.trail = (
                    f"{new_parent.trail}.{updated.id}"
                    if new_parent
                    else str(updated.id)
                )
            if old_trail != updated.trail:
                await self._update_descendants_trail(old_trail, updated.trail)

            # ③ path 仅用户显式改才重算（移动不动 URL）
            if old_path != updated.path:
                if updated.parent_id:
                    updated.parent = new_parent or await self.repository.get(
                        updated.parent_id, load=[Category.parent]
                    )
                else:
                    updated.parent = None
                updated.path = normalize_path(self._generate_path(updated))
                # 跨表 path 唯一校验(与 create 对齐): Category path 与 Page/Content
                # path 跨表无 DB 约束, 重算后必须校验, 排除自身 id。
                await check_path_unique(
                    self.repository.session, updated.path, exclude_id=updated.id
                )

            updated.content_path = normalize_path(updated.content_path)
        except Exception:
            try:
                await self.repository.session.rollback()
            except Exception:
                pass  # 连接断开等极端情况, 优先保留原始异常
            raise
        return updated

    async def _resolve_parent(self, parent_id, current_node):
        """加载新父栏目，若成环则拒绝。返回新父对象或 None（顶级）。"""
        if not parent_id:
            return None
        parent = await self.repository.get(parent_id, load=[Category.parent])
        if parent.trail == current_node.trail or parent.trail.startswith(
            f"{current_node.trail}."
        ):
            raise ClientException(
                "不能移动到自己的子孙栏目下", status_code=HTTP_409_CONFLICT
            )
        return parent

    async def _update_descendants_trail(self, old_trail: str, new_trail: str) -> None:
        """将子孙节点 trail 中的旧前缀替换为新前缀。"""
        stmt = (
            update(Category)
            .where(Category.trail.like(f"{old_trail}.%"))
            .values(trail=func.replace(Category.trail, old_trail, new_trail))
        )
        await self.repository.session.execute(stmt)

    def _generate_path(self, model_instance):
        return build_permalink(model_instance.path, model_instance)


class ContentAssociationServiceMixin(PaginationServiceMixin, Generic[ModelT]):
    """
    为拥有 contents M2M 关系的 taxonomy 服务提供批量关联/移除能力。
    依赖子类 repository.model_type 上存在 contents 关系属性。
    """

    async def attach_contents(self, item_id: UUID, content_ids: list[UUID]) -> None:
        """批量将内容关联到当前对象"""
        if not content_ids:
            return

        item = await self.get(
            item_id, load=[selectinload(self.repository.model_type.contents)]
        )
        existing_ids = {c.id for c in item.contents}
        pending_ids = [cid for cid in content_ids if cid not in existing_ids]
        if not pending_ids:
            return

        content_repo = ContentRepository(session=self.repository.session)
        contents = await content_repo.list(
            CollectionFilter(field_name="id", values=pending_ids),
        )
        item.contents.extend(contents)

    async def detach_contents(self, item_id: UUID, content_ids: list[UUID]) -> None:
        """批量从当前对象移除内容"""
        if not content_ids:
            return

        item = await self.get(
            item_id, load=[selectinload(self.repository.model_type.contents)]
        )
        existing = {c.id: c for c in item.contents}
        to_remove = [existing[cid] for cid in content_ids if cid in existing]
        if not to_remove:
            return

        for content in to_remove:
            item.contents.remove(content)


class TagService(
    ContentAssociationServiceMixin, SQLAlchemyAsyncRepositoryService[Tag]
):
    repository_type = TagRepository

    async def to_model_on_create(self, data: ModelDictT[Tag]) -> ModelDictT[Tag]:
        """表单没传 slug 时自动生成（中文转拼音，英文保留，冲突加数字后缀）。"""
        if not is_dict(data):
            data = schema_dump(data)

        slug = data.get("slug")
        if not slug or not str(slug).strip():
            result = await self.repository.session.execute(select(Tag.slug))
            existing_slugs = set(result.scalars().all())
            data["slug"] = _make_tag_slug(data.get("name", ""), existing_slugs)

        data["id"] = uuid7()
        return await super().to_model(data)

    async def resolve_tags(self, names: list[str]) -> list[Tag]:
        """
        把标签名批量解析为 Tag 对象：已存在的直接返回，不存在的自动创建。
        大小写不敏感去重，保留首次出现顺序。用于文章保存时关联标签。

        注意：此方法直接操作 session，而非通过 self.create()/self.repository.add()，
        因为需要 SAVEPOINT 精确控制每个 tag 的 flush 时机 —— service/repository
        层 API 未暴露此粒度的控制。
        """
        if not names:
            return []
        unique_names = list(dict.fromkeys(n.strip() for n in names if n.strip()))
        if not unique_names:
            return []

        session = self.repository.session

        # 查已存在的 Tag（大小写不敏感）
        stmt = select(Tag).where(
            func.lower(Tag.name).in_([n.lower() for n in unique_names])
        )
        existing = list((await session.execute(stmt)).scalars().all())
        existing_lower = {t.name.lower(): t for t in existing}

        # 查现有 slug，用于冲突检测
        existing_slugs = set((await session.execute(select(Tag.slug))).scalars().all())

        result = []
        for name in unique_names:
            key = name.lower()
            if key in existing_lower:
                result.append(existing_lower[key])
                continue

            slug = _make_tag_slug(name, existing_slugs)
            while True:
                try:
                    async with session.begin_nested():
                        new_tag = Tag(id=uuid7(), name=name, slug=slug)
                        session.add(new_tag)
                        await session.flush()
                    result.append(new_tag)
                    existing_lower[key] = new_tag
                    existing_slugs.add(slug)
                    break
                except IntegrityError:
                    # SAVEPOINT 已自动 rollback, 外层事务不受影响
                    concurrent = (
                        await session.execute(
                            select(Tag).where(func.lower(Tag.name) == key)
                        )
                    ).scalar_one_or_none()
                    if concurrent is not None:
                        # 同名并发插入: 复用已有
                        result.append(concurrent)
                        existing_lower[key] = concurrent
                        existing_slugs.add(concurrent.slug)
                        break
                    # 不同名但 slug 撞车(拼音相同): 重新生成 slug 后循环重试
                    existing_slugs.add(slug)
                    slug = _make_tag_slug(name, existing_slugs)
        return result


class SpecialService(
    ContentAssociationServiceMixin, SQLAlchemyAsyncRepositoryService[Special]
):
    repository_type = SpecialRepository


class FeatureService(
    ContentAssociationServiceMixin, SQLAlchemyAsyncRepositoryService[Feature]
):
    repository_type = FeatureRepository

    async def to_model_on_create(
        self, data: ModelDictT[Feature]
    ) -> ModelDictT[Feature]:
        """表单没传 slug 时自动生成（中文转拼音，英文保留，冲突加数字后缀）。"""
        if not is_dict(data):
            data = schema_dump(data)

        slug = data.get("slug")
        if not slug or not str(slug).strip():
            result = await self.repository.session.execute(select(Feature.slug))
            existing_slugs = set(result.scalars().all())
            data["slug"] = _make_feature_slug(data.get("name", ""), existing_slugs)

        data["id"] = uuid7()
        return await super().to_model(data)
