from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset, SearchFilter
from litestar import Controller, delete, get, patch, post
from litestar.params import Parameter
from sqlalchemy.orm import lazyload

from application.deps import create_service_provider
from application.guards import PermissionGuard

from ..schemas import RoleCreateSchema, RoleLiteSchema, RoleSchema, RoleUpdateSchema
from ..services import RoleService

if TYPE_CHECKING:
    from advanced_alchemy.service import OffsetPagination


view_permission = PermissionGuard("accounts:view_role", "查看角色")
create_permission = PermissionGuard("accounts:create_role", "创建角色")
update_permission = PermissionGuard("accounts:update_role", "更新角色")
delete_permission = PermissionGuard("accounts:delete_role", "删除角色")


class RoleController(Controller):
    path = "/roles"
    tags = ["roles (角色)"]

    dependencies = {
        "service": create_service_provider(RoleService),
    }

    @get(guards=[view_permission])
    async def list_roles(
        self,
        service: RoleService,
        limit_offset: LimitOffset,
        search: Annotated[str | None, Parameter(default=None)],
    ) -> OffsetPagination[RoleLiteSchema]:
        filters = []
        if search:
            filters.append(SearchFilter(field_name="name", value=search))

        filters.append(limit_offset)
        # 执行查询
        results, total = await service.list_and_count(*filters, load=[lazyload("*")])
        return service.to_schema(
            data=results, total=total, schema_type=RoleLiteSchema, filters=filters
        )

    @get("{item_id:uuid}", guards=[view_permission])
    async def get_role(self, service: RoleService, item_id: UUID) -> RoleSchema:
        role = await service.get(item_id)
        return service.to_schema(data=role, schema_type=RoleSchema)

    @post(guards=[create_permission])
    async def create_role(
        self,
        service: RoleService,
        data: RoleCreateSchema,
    ) -> RoleSchema:
        role = await service.create(data)
        return service.to_schema(
            data=role,
            schema_type=RoleSchema,
        )

    @patch("{item_id:uuid}", guards=[update_permission])
    async def update_role(
        self,
        service: RoleService,
        data: RoleUpdateSchema,
        item_id: UUID,
    ) -> RoleSchema:
        role = await service.update(data, item_id)
        return service.to_schema(data=role, schema_type=RoleSchema)

    @delete("{item_id:uuid}", guards=[delete_permission])
    async def delete_role(self, service: RoleService, item_id: UUID) -> None:
        await service.delete(item_id)
