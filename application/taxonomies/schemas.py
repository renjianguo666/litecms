from __future__ import annotations

from datetime import datetime
from uuid import UUID

from msgspec import field as msgspec_field

from application.schemas import Schema


class CategorySchema(Schema):
    """栏目展示层 Schema（search 模式列表用）。"""

    id: UUID
    name: str
    title: str | None
    description: str | None
    cover_url: str | None
    path: str
    content_path: str
    page_size: int
    trail: str
    priority: int
    template: str | None
    domain: str | None
    parent_id: UUID | None
    created_at: datetime
    updated_at: datetime
    url: str
    absolute_url: str

    children: list[CategorySchema] = msgspec_field(default_factory=list)


class SpecialSchema(Schema):
    """专题展示层 Schema。"""

    id: UUID
    name: str
    slug: str
    title: str
    description: str | None
    cover_url: str | None
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime

    url: str
    absolute_url: str


class FeatureSchema(Schema):
    """推荐位展示层 Schema。"""

    id: UUID
    name: str
    slug: str
    is_active: bool | str
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        super().__post_init__()
        self.is_active = "是" if self.is_active else "否"


class TagSchema(Schema):
    """标签展示层 Schema。"""

    id: UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime

    url: str
    absolute_url: str
