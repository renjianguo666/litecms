from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset, SearchFilter
from advanced_alchemy.service import OffsetPagination
from litestar import Controller, delete, get, patch, post
from litestar.params import Parameter
from sqlalchemy.orm import lazyload

from application.deps import create_service_provider
from application.guards import PermissionGuard

from ..schemas import (
    TagCreateSchema,
    TagSchema,
    TagUpdateSchema,
)
from ..services import TagService

view_permission = PermissionGuard("taxonomies:view_tag", "查看标签")
create_permission = PermissionGuard("taxonomies:create_tag", "创建标签")
update_permission = PermissionGuard("taxonomies:update_tag", "更新标签")
delete_permission = PermissionGuard("taxonomies:delete_tag", "删除标签")


class TagController(Controller):
    path = "/tags"
    tags = ["Taxonomy (标签)"]

    dependencies = {"service": create_service_provider(TagService)}

    @get(guards=[view_permission])
    async def list_tags(
        self,
        service: TagService,
        limit_offset: LimitOffset,
        search: Annotated[str | None, Parameter(default=None)],
    ) -> OffsetPagination[TagSchema]:
        filters = []
        if search:
            filters.append(
                SearchFilter(field_name="name", value=search, ignore_case=True)
            )

        filters.append(limit_offset)

        results, total = await service.list_and_count(*filters, load=lazyload("*"))

        return service.to_schema(
            data=results,
            total=total,
            schema_type=TagSchema,
            filters=filters,
        )

    @get("{item_id:uuid}", guards=[view_permission])
    async def get_tag(
        self,
        item_id: UUID,
        service: TagService,
    ) -> TagSchema:
        tag = await service.get(item_id)
        return service.to_schema(
            data=tag,
            schema_type=TagSchema,
        )

    @post(guards=[create_permission])
    async def create_tag(self, service: TagService, data: TagCreateSchema) -> TagSchema:
        tag = await service.create(data)
        return service.to_schema(
            data=tag,
            schema_type=TagSchema,
        )

    @patch("{item_id:uuid}", guards=[update_permission])
    async def update_tag(
        self,
        item_id: UUID,
        service: TagService,
        data: TagUpdateSchema,
    ) -> TagSchema:
        tag = await service.update(data, item_id)
        return service.to_schema(
            data=tag,
            schema_type=TagSchema,
        )

    @delete("{item_id:uuid}", guards=[delete_permission])
    async def delete_tag(self, item_id: UUID, service: TagService) -> None:
        await service.delete(item_id)
