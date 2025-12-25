from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.base import AdvancedDeclarativeBase, UUIDv7AuditBase, UUIDv7Base
from advanced_alchemy.types import HashedPassword, PasswordHash
from advanced_alchemy.types.password_hash.argon2 import Argon2Hasher
from sqlalchemy import ForeignKey, String, sql
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from application.contents.models import Content


class User(UUIDv7AuditBase):
    """
    用户模型 (User)
    """

    __tablename__ = "accounts_users"

    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[HashedPassword] = mapped_column(
        PasswordHash(backend=Argon2Hasher())
    )
    is_active: Mapped[bool] = mapped_column(server_default=sql.true(), index=True)
    is_superuser: Mapped[bool] = mapped_column(server_default=sql.false())

    # 关系: User <-> Role (多对多)
    # 我们使用 `lazy="selectin"` 来避免 N+1 查询, 这对异步友好
    roles: Mapped[list[Role]] = relationship(
        secondary="accounts_users_roles",  # 引用下面的关联表名称
        back_populates="users",
        lazy="selectin",
    )

    contents: Mapped[list[Content]] = relationship(
        back_populates="creator", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<User username='{self.username}' id='{self.id}'>"

    def has_permission(self, permission: str) -> bool:
        return any(
            permission in [p.name for p in role.permissions] for role in self.roles
        )

    @property
    def permission_names(self) -> list[str]:
        """返回用户所有权限名称列表，超级用户返回通配符"""
        if self.is_superuser:
            return ["*"]
        return list({p.name for role in self.roles for p in role.permissions})


class Role(UUIDv7Base):
    """
    角色模型 (Role)
    """

    __tablename__ = "accounts_roles"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255))

    # 关系: Role <-> User (多对多)
    users: Mapped[list[User]] = relationship(
        secondary="accounts_users_roles", back_populates="roles"
    )

    # 关系: Role <-> Permission (多对多)
    permissions: Mapped[list[Permission]] = relationship(
        secondary="accounts_roles_permissions", back_populates="roles", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Role name='{self.name}' id='{self.id}'>"


class Permission(UUIDv7Base):
    """
    权限模型 (Permission)
    """

    __tablename__ = "accounts_permissions"

    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255))

    # 关系: Permission <-> Role (多对多)
    roles: Mapped[list[Role]] = relationship(
        secondary="accounts_roles_permissions",
        back_populates="permissions",
        lazy="raise",
    )

    def __repr__(self) -> str:
        return f"<Permission name='{self.name}'>"


class UserRole(AdvancedDeclarativeBase):
    """
    用户-角色 关联表 (多对多)
    """

    __tablename__ = "accounts_users_roles"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts_users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts_roles.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,  # 反向索引：查询某角色的所有用户
    )


class RolePermission(AdvancedDeclarativeBase):
    """
    角色-权限 关联表 (多对多)
    """

    __tablename__ = "accounts_roles_permissions"

    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts_roles.id", ondelete="CASCADE"), primary_key=True
    )
    permission_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts_permissions.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,  # 反向索引：查询某权限的所有角色
    )
