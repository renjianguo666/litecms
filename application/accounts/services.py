from __future__ import annotations

from uuid import UUID

from advanced_alchemy.filters import CollectionFilter
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import (
    SQLAlchemyAsyncRepositoryService,
    schema_dump,
    typing,
)
from litestar.exceptions import ClientException
from litestar.status_codes import HTTP_409_CONFLICT
from sqlalchemy import func, select
from sqlalchemy.orm import lazyload

from .models import Permission, Role, User


class PermissionRepository(SQLAlchemyAsyncRepository[Permission]):
    model_type = Permission


class RoleRepository(SQLAlchemyAsyncRepository[Role]):
    model_type = Role


class UserRepository(SQLAlchemyAsyncRepository[User]):
    model_type = User


class PermissionService(SQLAlchemyAsyncRepositoryService[Permission]):
    repository_type = PermissionRepository


class RoleService(SQLAlchemyAsyncRepositoryService[Role]):
    repository_type = RoleRepository

    async def to_model_on_create(
        self, data: typing.ModelDictT[User]
    ) -> typing.ModelDictT[User]:
        if not isinstance(data, dict):
            data = schema_dump(data)

        permission_ids = data.get("permissions", [])
        if permission_ids:
            perm_repo = PermissionRepository(session=self.repository.session)
            data["permissions"] = await perm_repo.list(
                CollectionFilter(field_name="id", values=permission_ids),
                load=lazyload("*"),
            )
        return data

    async def to_model_on_update(
        self, data: typing.ModelDictT[User]
    ) -> typing.ModelDictT[User]:
        if not isinstance(data, dict):
            data = schema_dump(data)
        """
        msgspec UNSET 的处理:
            UserUpdateSchema 使用了 msgspec.UNSET,
            schema_dump() 会自动排除未设置的字段
            所以 data.get("roles", None) 会返回 None
        """
        permission_ids = data.get("permissions", None)
        if permission_ids is not None:
            perm_repo = PermissionRepository(session=self.repository.session)
            data["permissions"] = await perm_repo.list(
                CollectionFilter(field_name="id", values=permission_ids),
                load=lazyload("*"),
            )
        return data


class UserService(SQLAlchemyAsyncRepositoryService[User]):
    repository_type = UserRepository

    async def delete(
        self,
        item_id: UUID,
        **kwargs,
    ) -> User:
        """删除用户，预检查关联数据

        Parameters
        ----------
        item_id : UUID
            用户 ID

        Returns
        -------
        User
            被删除的用户

        Raises
        ------
        ClientException
            用户有关联文章时抛出
        """
        # 延迟导入避免循环依赖
        from application.contents.models import Content

        # 检查用户是否有关联的文章
        stmt = (
            select(func.count())
            .select_from(Content)
            .where(Content.creator_id == item_id)
        )
        result = await self.repository.session.execute(stmt)
        content_count = result.scalar() or 0

        if content_count > 0:
            raise ClientException(
                detail=f"无法删除该用户，该用户还有 {content_count} 篇关联内容",
                status_code=HTTP_409_CONFLICT,
            )

        return await super().delete(item_id, **kwargs)

    async def to_model_on_create(
        self, data: typing.ModelDictT[User]
    ) -> typing.ModelDictT[User]:
        if not isinstance(data, dict):
            data = schema_dump(data)

        # 检查用户名是否已存在
        existing = await self.get_one_or_none(username=data.get("username"))
        if existing:
            raise ClientException("用户名已存在", status_code=HTTP_409_CONFLICT)

        role_ids = data.get("roles", [])
        if role_ids:
            role_repo = RoleRepository(session=self.repository.session)
            data["roles"] = await role_repo.list(
                CollectionFilter(field_name="id", values=role_ids), load=lazyload("*")
            )
        return data

    async def to_model_on_update(
        self, data: typing.ModelDictT[User]
    ) -> typing.ModelDictT[User]:
        if not isinstance(data, dict):
            data = schema_dump(data)
        """
        msgspec UNSET 的处理:
            UserUpdateSchema 使用了 msgspec.UNSET,
            schema_dump() 会自动排除未设置的字段
            所以 data.get("roles", None) 会返回 None
        """
        role_ids = data.get("roles", None)
        if role_ids is not None:
            role_repo = RoleRepository(session=self.repository.session)
            data["roles"] = await role_repo.list(
                CollectionFilter(field_name="id", values=role_ids),
                load=lazyload("*"),
            )
        return data
