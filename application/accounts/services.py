from __future__ import annotations

from typing import Any

from advanced_alchemy.filters import CollectionFilter
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import (
    SQLAlchemyAsyncRepositoryService,
    schema_dump,
)
from advanced_alchemy.service import typing as service_typing
from sqlalchemy.orm import selectinload

from application.contents.models import Content
from application.contents.services import ContentRepository
from application.mixins import PaginationServiceMixin

from .models import Permission, Role, User


class PermissionRepository(SQLAlchemyAsyncRepository[Permission]):
    model_type = Permission


class RoleRepository(SQLAlchemyAsyncRepository[Role]):
    model_type = Role


class UserRepository(SQLAlchemyAsyncRepository[User]):
    model_type = User


class PermissionService(
    PaginationServiceMixin, SQLAlchemyAsyncRepositoryService[Permission]
):
    repository_type = PermissionRepository


class RoleService(PaginationServiceMixin, SQLAlchemyAsyncRepositoryService[Role]):
    repository_type = RoleRepository

    async def to_model_on_create(
        self, data: service_typing.ModelDictT[Role]
    ) -> service_typing.ModelDictT[Role]:
        if not isinstance(data, dict):
            data = schema_dump(data)

        permission_ids = data.get("permissions", None)
        if permission_ids is not None:
            perm_repo = PermissionRepository(session=self.repository.session)
            data["permissions"] = await perm_repo.get_many(
                CollectionFilter(field_name="id", values=permission_ids)
            )
        return data

    async def update(
        self, data: service_typing.ModelDictT[Role], item_id: Any | None = None, **kwargs: Any
    ) -> Role:
        """重写 update: permissions 是 M2M 关系, 同上用原生 ORM 同步 (避免 SAWarning)。"""
        permission_ids = None
        if isinstance(data, dict) and "permissions" in data:
            permission_ids = data.pop("permissions")
        updated = await super().update(data, item_id, **kwargs)
        if permission_ids is not None:
            permissions = await PermissionRepository(
                session=self.repository.session
            ).get_many(CollectionFilter(field_name="id", values=permission_ids))
            role = await self.repository.get(item_id, load=[selectinload(Role.permissions)])
            role.permissions = list(permissions)
            await self.repository.session.flush()
        return updated


class UserService(PaginationServiceMixin, SQLAlchemyAsyncRepositoryService[User]):
    repository_type = UserRepository

    async def delete(self, item_id: Any, **kwargs: Any) -> None:
        await ContentRepository(session=self.repository.session).delete_where(
            Content.creator_id == item_id,
        )
        await super().delete(item_id, **kwargs)

    async def to_model_on_create(
        self, data: service_typing.ModelDictT[User]
    ) -> service_typing.ModelDictT[User]:
        if not isinstance(data, dict):
            data = schema_dump(data)

        alias = data.get("alias")
        if not alias:  # 如果 alias 为 None 或空字符串
            data["alias"] = data["username"]

        role_ids = data.get("roles", None)
        if role_ids is not None:
            role_repo = RoleRepository(session=self.repository.session)
            data["roles"] = await role_repo.get_many(
                CollectionFilter(field_name="id", values=role_ids)
            )
        return data

    async def update(
        self, data: service_typing.ModelDictT[User], item_id: Any | None = None, **kwargs: Any
    ) -> User:
        """重写 update: roles 是 M2M 关系, advanced_alchemy 的 service.update 对其会触发
        SAWarning (官方 fullstack 同样触发, 见 issue)。抽出 roles 后用原生 ORM 同步,
        普通字段走 super().update。"""
        role_ids = None
        if isinstance(data, dict) and "roles" in data:
            role_ids = data.pop("roles")
        updated = await super().update(data, item_id, **kwargs)
        if role_ids is not None:
            roles = await RoleRepository(session=self.repository.session).get_many(
                CollectionFilter(field_name="id", values=role_ids)
            )
            user = await self.repository.get(item_id, load=[selectinload(User.roles)])
            user.roles = list(roles)
            await self.repository.session.flush()
        return updated
