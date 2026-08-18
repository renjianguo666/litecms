from __future__ import annotations

from typing import Any

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService, schema_dump
from advanced_alchemy.service.typing import ModelDictT
from litestar.utils.path import normalize_path

from application.checks import check_path_unique
from application.mixins import PaginationServiceMixin
from application.sanitizer import sanitize_html

from .models import Page


class PageRepository(SQLAlchemyAsyncRepository[Page]):
    model_type = Page


class PageService(PaginationServiceMixin, SQLAlchemyAsyncRepositoryService[Page]):
    repository_type = PageRepository

    async def to_model_on_create(
        self, data: ModelDictT[Page]
    ) -> ModelDictT[Page]:
        data = schema_dump(data)
        data["path"] = normalize_path(data["path"])
        await check_path_unique(self.repository.session, data["path"])
        data["text"] = sanitize_html(data.get("text", ""))
        return await super().to_model_on_create(data)

    async def update(
        self, data: ModelDictT[Page], item_id: Any | None = None, **kwargs
    ) -> Page:
        data = schema_dump(data)
        data["path"] = normalize_path(data["path"])
        data["text"] = sanitize_html(data.get("text", ""))
        history = await self.repository.get(item_id)
        if data["path"] != history.path:
            await check_path_unique(self.repository.session, data["path"])
        return await super().update(data=data, item_id=item_id, **kwargs)
