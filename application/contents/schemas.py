from __future__ import annotations

from datetime import datetime
from uuid import UUID

from application.contents.enums import PublishStatus
from application.schemas import Schema


class ContentSchema(Schema):
    """内容展示层 Schema（文章/单页列表、管理页通用）。

    category_name / creator_username 是 Content 的 hybrid_property，
    convert(from_attributes=True) 会当普通属性读取，无需特殊处理。
    不声明 tags/specials/features/creator/category 等 lazy="raise" 关系，避免触发。
    polymorphic_type 是 SQLAlchemy 多态内部标识，非展示字段，不声明。
    creator_id / category_id 为外键，遵循 PageSchema/UserSchema 惯例不暴露，
    用 creator_username / category_name 展示关联。
    """

    id: UUID
    title: str
    path: str
    description: str | None
    cover_url: str | None
    source: str | None
    author: str | None
    status: PublishStatus
    views: int
    published_at: datetime
    created_at: datetime
    updated_at: datetime
    creator_username: str
    category_id: UUID
    category_name: str
    url: str
    absolute_url: str
