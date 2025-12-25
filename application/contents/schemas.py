from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from application.accounts.schemas import UserLiteSchema
from application.contents.enums import PublishStatus
from application.taxonomies.schemas import (
    CategoryLiteSchema,
    FeatureLiteSchema,
    TagLiteSchema,
    SpecialLiteSchema,
)


class ContentLiteSchema(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    title: str
    path: str
    url: str
    description: str | None = None
    cover_url: str | None = None
    status: PublishStatus
    views: int
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    category_id: UUID
    category: CategoryLiteSchema
    creator_id: UUID
    creator: UserLiteSchema


class ContentSchema(ContentLiteSchema):
    tags: list[TagLiteSchema]
    specials: list[SpecialLiteSchema]
    features: list[FeatureLiteSchema]
