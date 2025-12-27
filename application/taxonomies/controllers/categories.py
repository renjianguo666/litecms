from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset, SearchFilter
from advanced_alchemy.service import OffsetPagination
from litestar import Controller, Request, delete, get, patch, post
from litestar.params import Parameter
from sqlalchemy.orm import lazyload

from application.deps import create_service_provider
from application.guards import PermissionGuard

from ..models import Category
from ..schemas import (
    CategoryCreateSchema,
    CategoryLiteSchema,
    CategorySchema,
    CategoryUpdateSchema,
)
from ..services import CategoryService

view_permission = PermissionGuard("taxonomies:view_category", "查看栏目")
create_permission = PermissionGuard("taxonomies:create_category", "创建栏目")
update_permission = PermissionGuard("taxonomies:update_category", "更新栏目")
delete_permission = PermissionGuard("taxonomies:delete_category", "删除栏目")


class CategoryController(Controller):
    path = "/categories"
    tags = ["Taxonomy (分类)"]

    dependencies = {"service": create_service_provider(CategoryService)}

    @get(guards=[view_permission])
    async def list_categories(
        self,
        service: CategoryService,
        page: Annotated[int, Parameter(default=1)],
        page_size: Annotated[int, Parameter(default=50)],
        search: Annotated[str | None, Parameter(default=None)],
    ) -> OffsetPagination[CategoryLiteSchema]:
        filters = []
        if search:
            filters.append(
                SearchFilter(field_name="name", value=search, ignore_case=True)
            )

        filters.append(LimitOffset(limit=page_size, offset=page_size * (page - 1)))
        results, total = await service.list_and_count(
            *filters,
            load=lazyload("*"),
            order_by=[Category.trail.asc(), Category.priority.desc()],
        )

        return service.to_schema(
            data=results,
            total=total,
            schema_type=CategoryLiteSchema,
            filters=filters,
        )

    @get("{item_id:uuid}", guards=[view_permission])
    async def get_category(
        self,
        item_id: UUID,
        service: CategoryService,
    ) -> CategorySchema:
        category = await service.get(item_id)
        return service.to_schema(
            data=category,
            schema_type=CategorySchema,
        )

    @post(guards=[create_permission])
    async def create_category(
        self,
        service: CategoryService,
        data: CategoryCreateSchema,
        request: Request,
    ) -> CategoryLiteSchema:
        category = await service.create(data)
        request.app.emit("category_changed")
        return service.to_schema(
            data=category,
            schema_type=CategoryLiteSchema,
        )

    @patch("{item_id:uuid}", guards=[update_permission])
    async def update_category(
        self,
        item_id: UUID,
        service: CategoryService,
        data: CategoryUpdateSchema,
        request: Request,
    ) -> CategorySchema:
        category = await service.update(data, item_id)
        request.app.emit("category_changed")
        return service.to_schema(
            data=category,
            schema_type=CategorySchema,
        )

    @delete("{item_id:uuid}", guards=[delete_permission])
    async def delete_category(
        self, item_id: UUID, service: CategoryService, request: Request
    ) -> None:
        await service.delete(item_id)
        request.app.emit("category_changed")
