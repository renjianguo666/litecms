from __future__ import annotations

from datetime import datetime
from uuid import UUID

from application.accounts.schemas import UserLiteSchema
from application.contents.enums import PublishStatus
from application.schemas import Schema
from application.taxonomies.schemas import (
    CategoryLiteSchema,
    FeatureSchema,
    SpecialSchema,
    TagSchema,
)


class ContentLiteSchema(Schema):
    """内容轻量展示（列表用, 含 category/creator 嵌套, 查询时需 load 二者）。"""

    id: UUID
    title: str
    url: str
    absolute_url: str
    description: str | None
    cover_url: str | None
    source: str | None
    author: str | None
    views: int
    published_at: datetime
    created_at: datetime
    category: CategoryLiteSchema
    creator: UserLiteSchema


class ContentSchema(ContentLiteSchema):
    """内容完整展示（详情用, 补管理字段与多对多集合, 查询时需 load 全部）。"""

    path: str
    status: PublishStatus
    updated_at: datetime
    category_id: UUID
    tags: list[TagSchema]
    specials: list[SpecialSchema]
    features: list[FeatureSchema]
