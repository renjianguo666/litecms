from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import (
    ComparisonFilter,
    LimitOffset,
    OrderBy,
    SearchFilter,
)
from advanced_alchemy.service import OffsetPagination
from litestar import Controller, Request, delete, get, patch, post
from litestar.params import Parameter
from sqlalchemy.orm import lazyload

from application.deps import create_service_provider
from application.guards import PermissionGuard

from ..schemas import (
    SpecialCreateSchema,
    SpecialSchema,
    SpecialUpdateSchema,
)
from ..services import SpecialService

view_permission = PermissionGuard("taxonomies:view_special", "查看专题")
create_permission = PermissionGuard("taxonomies:create_special", "创建专题")
update_permission = PermissionGuard("taxonomies:update_special", "更新专题")
delete_permission = PermissionGuard("taxonomies:delete_special", "删除专题")


class SpecialController(Controller):
    path = "/specials"
    tags = ["Taxonomy (专题)"]

    dependencies = {"service": create_service_provider(SpecialService)}

    @get(guards=[view_permission])
    async def list_specials(
        self,
        service: SpecialService,
        limit_offset: LimitOffset,
        search: Annotated[
            str | None, Parameter(default=None, description="搜索名称/标题")
        ],
        is_active: Annotated[
            bool | None, Parameter(default=None, description="上线状态")
        ],
    ) -> OffsetPagination[SpecialSchema]:
        filters = []

        if search:
            filters.append(
                SearchFilter(field_name="name", value=search, ignore_case=True)
            )

        if is_active is not None:
            filters.append(
                ComparisonFilter(field_name="is_active", operator="eq", value=is_active)
            )

        # 默认按优先级降序、创建时间降序排列
        filters.append(OrderBy(field_name="priority", sort_order="desc"))
        filters.append(OrderBy(field_name="created_at", sort_order="desc"))
        filters.append(limit_offset)

        results, total = await service.list_and_count(*filters, load=lazyload("*"))

        return service.to_schema(
            data=results,
            total=total,
            schema_type=SpecialSchema,
            filters=filters,
        )

    @get("{special_id:uuid}", guards=[view_permission])
    async def get_special(
        self,
        special_id: UUID,
        service: SpecialService,
    ) -> SpecialSchema:
        special = await service.get(special_id)
        return service.to_schema(
            data=special,
            schema_type=SpecialSchema,
        )

    @post(guards=[create_permission])
    async def create_special(
        self, service: SpecialService, data: SpecialCreateSchema, request: Request
    ) -> SpecialSchema:
        special = await service.create(data)
        request.app.emit("special_changed")
        return service.to_schema(
            data=special,
            schema_type=SpecialSchema,
        )

    @patch("{special_id:uuid}", guards=[update_permission])
    async def update_special(
        self,
        special_id: UUID,
        service: SpecialService,
        data: SpecialUpdateSchema,
        request: Request,
    ) -> SpecialSchema:
        special = await service.update(data, special_id)
        request.app.emit("special_changed")
        return service.to_schema(
            data=special,
            schema_type=SpecialSchema,
        )

    @delete("{special_id:uuid}", guards=[delete_permission])
    async def delete_special(
        self, special_id: UUID, service: SpecialService, request: Request
    ) -> None:
        await service.delete(special_id)
        request.app.emit("special_changed")
