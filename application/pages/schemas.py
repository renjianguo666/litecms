from __future__ import annotations

from datetime import datetime
from uuid import UUID

from application.schemas import Schema


class PageSchema(Schema):
    """单页展示层 Schema（前后台共用）。"""

    id: UUID
    title: str
    path: str
    is_active: bool | str
    created_at: datetime
    updated_at: datetime
    url: str
    absolute_url: str
    description: str | None
    cover_url: str | None
    text: str
    template: str | None

    def __post_init__(self) -> None:
        super().__post_init__()
        self.is_active = "启用" if self.is_active else "禁用"
