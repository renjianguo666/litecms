from __future__ import annotations

from datetime import datetime
from os.path import splitext
from typing import Any

import sqlalchemy as sa
from advanced_alchemy.exceptions import RepositoryError
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import (
    SQLAlchemyAsyncRepositoryService,
    schema_dump,
)
from advanced_alchemy.service.typing import ModelDictT
from litestar.utils.path import normalize_path
from uuid_utils import uuid7

from application.utils import build_permalink

from .models import Category, Feature, Special, Tag


class CategoryRepository(SQLAlchemyAsyncRepository[Category]):
    model_type = Category


class TagRepository(SQLAlchemyAsyncRepository[Tag]):
    model_type = Tag


class SpecialRepository(SQLAlchemyAsyncRepository[Special]):
    model_type = Special


class FeatureRepository(SQLAlchemyAsyncRepository[Feature]):
    model_type = Feature


class CategoryService(SQLAlchemyAsyncRepositoryService[Category]):
    repository_type = CategoryRepository
    loader_options = [Category.parent]

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
        return model

    async def update(
        self, data: ModelDictT[Category], item_id: Any | None = None, **kwargs
    ) -> Category:
        model = await super().to_model(data, "update")
        pk_value = item_id or self.repository.get_id_attribute_value(
            data, id_attribute=kwargs["id_attribute"]
        )
        if pk_value is None:
            raise RepositoryError("Could not identify ID attribute value")

        history = await self.repository.get(pk_value)
        history_parent_id = history.parent_id
        history_trail = history.trail
        history_path = history.path

        kwargs["auto_commit"] = False
        updated = await super().update(model, item_id, **kwargs)

        if history_parent_id != updated.parent_id:
            if updated.parent:
                updated.trail = f"{updated.parent.trail}.{updated.id}"
            else:
                updated.trail = str(updated.id)

        if history_trail != updated.trail:
            await self._update_descendants_trail(history.trail, updated.trail)

        # permalink 变化 或 parent_id 变化（影响 {parent} 占位符）都需要重新生成
        if history_path != updated.path or history_parent_id != updated.parent_id:
            updated.path = normalize_path(self._generate_path(updated))

        updated.content_path = normalize_path(updated.content_path)
        await self.repository.session.commit()
        return updated

    async def _update_descendants_trail(self, old_prefix: str, new_prefix: str) -> None:
        """
        辅助方法：批量修复子孙节点的路径。
        原理：查找所有以 old_prefix 开头的 trail，把开头的 old_prefix 替换为 new_prefix。
        """
        # 构造查询模式：old.id.%
        # 加上 "." 是为了防止 UUID 部分匹配（虽然 UUID 冲突概率极低，但这是好习惯）
        search_pattern = f"{old_prefix}.%"

        stmt = (
            sa.update(self.repository.model_type)
            .where(self.repository.model_type.trail.like(search_pattern))
            .values(
                # 使用数据库层面的 REPLACE 函数，效率极高
                # update category set trail = replace(trail, 'old_str', 'new_str')
                trail=sa.func.replace(
                    self.repository.model_type.trail, old_prefix, new_prefix
                )
            )
        )
        # 执行批量更新
        await self.repository.session.execute(stmt)

    def _generate_path(self, model_instance):
        parent = model_instance.parent
        path = splitext(parent.path)[0] if parent else ""
        return build_permalink(
            rule=model_instance.path,
            dt=model_instance.created_at or datetime.now(),
            key=model_instance.id,
            parent=path,
        )


class TagService(SQLAlchemyAsyncRepositoryService[Tag]):
    repository_type = TagRepository


class SpecialService(SQLAlchemyAsyncRepositoryService[Special]):
    repository_type = SpecialRepository


class FeatureService(SQLAlchemyAsyncRepositoryService[Feature]):
    repository_type = FeatureRepository
