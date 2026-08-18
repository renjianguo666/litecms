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
    """用户模型"""

    __tablename__ = "accounts_users"

    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    alias: Mapped[str] = mapped_column(String(100), default="")
    password_hash: Mapped[HashedPassword] = mapped_column(
        PasswordHash(backend=Argon2Hasher())
    )
    is_active: Mapped[bool] = mapped_column(
        default=True, server_default=sql.true(), index=True
    )
    is_superuser: Mapped[bool] = mapped_column(
        default=False, server_default=sql.false()
    )

    roles: Mapped[list[Role]] = relationship(
        secondary="accounts_users_roles",
        back_populates="users",
        lazy="raise",
        passive_deletes=True,
    )

    contents: Mapped[list[Content]] = relationship(
        back_populates="creator", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<User username='{self.username}' id='{self.id}'>"

    def has_permission(self, code: str) -> bool:
        """检查用户是否拥有指定权限，超管直接通过"""
        if self.is_superuser:
            return True
        return code in self.permission_codes

    @property
    def permission_codes(self) -> set[str]:
        """返回用户所有权限名称集合，超级用户返回通配符"""
        if self.is_superuser:
            return {"*"}
        return {p.code for role in self.roles for p in role.permissions}

    def has_role(self, role_name: str) -> bool:
        """检查用户是否拥有指定角色"""
        return any(r.name == role_name for r in self.roles)


class Role(UUIDv7Base):
    """角色模型"""

    __tablename__ = "accounts_roles"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255))

    users: Mapped[list[User]] = relationship(
        secondary="accounts_users_roles",
        back_populates="roles",
        lazy="raise",
        passive_deletes=True,
    )

    permissions: Mapped[list[Permission]] = relationship(
        secondary="accounts_roles_permissions",
        back_populates="roles",
        lazy="raise",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Role name='{self.name}' id='{self.id}'>"


class Permission(UUIDv7Base):
    """权限模型"""

    __tablename__ = "accounts_permissions"

    code: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    group: Mapped[str] = mapped_column(String(255))

    roles: Mapped[list[Role]] = relationship(
        secondary="accounts_roles_permissions",
        passive_deletes=True,
        back_populates="permissions",
        lazy="raise",
    )

    def __repr__(self) -> str:
        return f"<Permission code='{self.code}' name='{self.name}'>"


class UserRole(AdvancedDeclarativeBase):
    """用户-角色 关联表"""

    __tablename__ = "accounts_users_roles"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts_users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts_roles.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )


class RolePermission(AdvancedDeclarativeBase):
    """角色-权限 关联表"""

    __tablename__ = "accounts_roles_permissions"

    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts_roles.id", ondelete="CASCADE"), primary_key=True
    )
    permission_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts_permissions.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
