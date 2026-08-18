from __future__ import annotations

from datetime import datetime
from uuid import UUID

from msgspec import field as msgspec_field

from application.schemas import Schema


class UserSchema(Schema):
    """用户展示层 Schema。"""

    id: UUID
    username: str
    alias: str
    is_active: bool | str
    is_superuser: bool | str
    created_at: datetime
    updated_at: datetime
    roles: list[RoleSchema] = msgspec_field(default_factory=list)

    def __post_init__(self) -> None:
        super().__post_init__()
        setattr(self, "is_active", "启用" if self.is_active else "禁用")
        setattr(self, "is_superuser", "是" if self.is_superuser else "否")
        setattr(
            self,
            "roles",
            " | ".join([r.name for r in self.roles]) if self.roles else "",
        )


class RoleSchema(Schema):
    """角色展示层 Schema（Role 继承 UUIDv7Base，无 audit 时间字段）。"""

    id: UUID
    name: str
    description: str | None
