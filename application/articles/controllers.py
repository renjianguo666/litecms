from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset, SearchFilter
from advanced_alchemy.service import OffsetPagination
from litestar import Controller, delete, get, patch, post
from litestar.params import Parameter
from sqlalchemy.orm import joinedload, selectinload, defer

from application.accounts.models import User
from application.deps import create_service_provider
from application.guards import PermissionGuard

from .models import Article
from .schemas import (
    ArticleCreateSchema,
    ArticleLiteSchema,
    ArticleSchema,
    ArticleUpdateSchema,
)
from .services import ArticleService

# 详情页加载选项：加载完整关联数据
DETAIL_LOAD_OPTIONS = [
    joinedload(Article.creator),
    joinedload(Article.category),
    selectinload(Article.tags),
    selectinload(Article.specials),
    selectinload(Article.features),
]

view_permission = PermissionGuard("articles:view_article", "查看文章")
create_permission = PermissionGuard("articles:create_article", "添加文章")
update_permission = PermissionGuard("articles:update_article", "更新文章")
delete_permission = PermissionGuard("articles:delete_article", "删除文章")


class ArticleController(Controller):
    path = "/articles"
    tags = ["Articles (文章)"]
    dependencies = {
        "service": create_service_provider(ArticleService),
    }

    @get(guards=[view_permission])
    async def list_articles(
        self,
        service: ArticleService,
        limit_offset: LimitOffset,
        search: Annotated[str | None, Parameter(default=None)],
    ) -> OffsetPagination[ArticleLiteSchema]:
        filters = []
        if search:
            filters.append(
                SearchFilter(field_name="title", value=search, ignore_case=True)
            )

        filters.append(limit_offset)
        total = await service.count(*filters)
        results = await service.list(
            *filters,
            load=[
                joinedload(Article.creator),
                joinedload(Article.category),
                defer(Article.text),
            ],
            order_by=Article.published_at.desc(),
        )
        return service.to_schema(
            data=results,
            total=total,
            schema_type=ArticleLiteSchema,
            filters=filters,
        )

    @get("{item_id:uuid}", guards=[view_permission])
    async def get_article(
        self,
        item_id: UUID,
        service: ArticleService,
    ) -> ArticleSchema:
        article = await service.get(item_id, load=DETAIL_LOAD_OPTIONS)
        return service.to_schema(
            data=article,
            schema_type=ArticleSchema,
        )

    @post(guards=[create_permission])
    async def create_article(
        self,
        service: ArticleService,
        current_user: User,
        data: ArticleCreateSchema,
    ) -> None:
        await service.create_many_for_categories(data, creator=current_user)

    @patch("{item_id:uuid}", guards=[update_permission])
    async def update_article(
        self,
        item_id: UUID,
        service: ArticleService,
        data: ArticleUpdateSchema,
    ) -> ArticleSchema:
        article = await service.update(data, item_id, load=DETAIL_LOAD_OPTIONS)
        return service.to_schema(
            data=article,
            schema_type=ArticleSchema,
        )

    @delete("{item_id:uuid}", guards=[delete_permission])
    async def delete_article(self, item_id: UUID, service: ArticleService) -> None:
        await service.delete(item_id)
