from __future__ import annotations

from uuid import UUID

from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService
from sqlalchemy import update

from application.mixins import PaginationServiceMixin

from .models import Content


class ContentRepository(SQLAlchemyAsyncRepository[Content]):
    model_type = Content


class ContentService(
    PaginationServiceMixin,
    SQLAlchemyAsyncRepositoryService[Content],
):
    repository_type = ContentRepository

    async def increment_views(self, item_id: UUID) -> int:
        result = await self.repository.session.execute(
            update(Content)
            .where(Content.id == item_id)
            .values(views=Content.views + 1)
            .returning(Content.views)
        )
        return result.scalar_one()
