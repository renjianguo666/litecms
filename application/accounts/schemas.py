from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# 1. 定义常量和类型
EMAIL_REGEX = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,63}$"

# 定义可复用的 Email 类型
Email = Annotated[str, Field(pattern=EMAIL_REGEX, description="邮箱地址")]


# ==========================================
# 2. Permission Schemas (最底层依赖)
# ==========================================


class PermissionSchema(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    name: str
    description: str | None = None


class PermissionCreateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, max_length=255, description="权限名称")
    description: str = Field(..., min_length=1, max_length=255, description="权限描述")


class PermissionUpdateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1, max_length=255)


# ==========================================
# 3. Role Schemas (依赖 Permission)
# ==========================================


class RoleLiteSchema(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    name: str
    description: str | None = None


class RoleSchema(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    permissions: list[PermissionSchema]


class RoleCreateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, max_length=100, description="角色名称")

    description: str | None = Field(
        default=None, min_length=1, max_length=255, description="角色描述"
    )
    permissions: list[UUID] | None = Field(default=None, description="权限ID列表")


class RoleUpdateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=255)
    permissions: list[UUID] | None = None


# ==========================================
# 4. User Schemas (依赖 Role)
# ==========================================


class UserLiteSchema(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    username: str
    email: Email | None = None
    is_active: bool
    is_superuser: bool
    created_at: datetime


class UserSchema(BaseModel):
    """用户信息"""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    username: str
    email: Email | None = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    roles: list[RoleLiteSchema]
    permissions: list[str] = Field(validation_alias="permission_names")


class UserCreateSchema(BaseModel):
    """创建用户账户"""

    model_config = ConfigDict(frozen=True)

    username: str = Field(..., min_length=2, max_length=100, description="用户名")
    email: Email | None = None

    # alias="password" 允许前端传 JSON {"password": "123"}，解析后变成 obj.password_hash
    password_hash: str = Field(..., alias="password", min_length=6, description="密码")

    is_superuser: bool = False  # 这里的默认值看业务需求，通常创建时默认为 False
    roles: list[UUID] | None = None


class UserUpdateSchema(BaseModel):
    """更新用户信息"""

    model_config = ConfigDict(frozen=True)

    username: str | None = Field(default=None, min_length=2, max_length=100)
    email: Email | None = None
    is_active: bool | None = None

    password_hash: str | None = Field(default=None, alias="password", min_length=6)
    roles: list[UUID] | None = None


class UserLoginSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    username: str
    password: str


class PasswordChangeSchema(BaseModel):
    """修改密码"""

    model_config = ConfigDict(frozen=True)

    old_password: str = Field(..., min_length=1, description="当前密码")
    new_password: str = Field(..., min_length=6, description="新密码")
