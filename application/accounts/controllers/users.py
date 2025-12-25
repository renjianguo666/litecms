from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import ComparisonFilter, LimitOffset, SearchFilter
from litestar import Controller, delete, get, patch, post
from litestar.pagination import OffsetPagination
from litestar.params import Parameter
from sqlalchemy.orm import lazyload

from application.deps import create_service_provider
from application.guards import PermissionGuard

from ..schemas import UserCreateSchema, UserLiteSchema, UserSchema, UserUpdateSchema
from ..services import UserService

view_permission = PermissionGuard("accounts:view_user", "查看用户")
create_permission = PermissionGuard("accounts:create_user", "创建用户")
update_permission = PermissionGuard("accounts:update_user", "更新用户")
delete_permission = PermissionGuard("accounts:delete_user", "删除用户")


class UserController(Controller):
    path = "/users"
    tags = ["users (用户)"]

    dependencies = {
        "service": create_service_provider(UserService),
    }

    @get(guards=[view_permission])
    async def list_users(
        self,
        service: UserService,
        limit_offset: LimitOffset,
        search: Annotated[str | None, Parameter(default=None)],
        is_active: Annotated[bool | None, Parameter(default=None)],
    ) -> OffsetPagination[UserLiteSchema]:
        filters = []
        if search:
            filters.append(
                SearchFilter(field_name="username", value=search, ignore_case=True)
            )
        if is_active is not None:
            filters.append(
                ComparisonFilter(field_name="is_active", operator="eq", value=is_active)
            )
        filters.append(limit_offset)
        # 执行查询
        results, total = await service.list_and_count(*filters, load=lazyload("*"))
        return service.to_schema(
            data=results, total=total, schema_type=UserLiteSchema, filters=filters
        )

    @get("{item_id:uuid}", guards=[view_permission])
    async def get_user(self, item_id: UUID, service: UserService) -> UserSchema:
        user = await service.get(item_id)
        return service.to_schema(data=user, schema_type=UserSchema)

    @post(guards=[create_permission])
    async def create_user(
        self, data: UserCreateSchema, service: UserService
    ) -> UserSchema:
        user = await service.create(data)
        return service.to_schema(data=user, schema_type=UserSchema)

    @patch("{item_id:uuid}", guards=[update_permission])
    async def update_user(
        self, item_id: UUID, data: UserUpdateSchema, service: UserService
    ) -> UserSchema:
        user = await service.update(data, item_id)
        return service.to_schema(data=user, schema_type=UserSchema)

    @delete("{item_id:uuid}", guards=[delete_permission])
    async def delete_user(self, item_id: UUID, service: UserService) -> None:
        await service.delete(item_id)
