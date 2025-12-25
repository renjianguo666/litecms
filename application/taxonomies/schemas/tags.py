from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from application.web.urls import build_tag_url

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class TagLiteSchema(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    name: str
    slug: str

    @computed_field
    @property
    def url(self) -> str:
        return build_tag_url(self.slug)


class TagSchema(TagLiteSchema):
    """标签完整信息"""

    created_at: datetime
    updated_at: datetime


class TagCreateSchema(BaseModel):
    """创建标签"""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, max_length=100, description="标签名称")

    slug: str = Field(
        ...,
        pattern=SLUG_PATTERN,
        max_length=100,
        description="URL 友好标识",
    )


class TagUpdateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str | None = Field(min_length=1, max_length=100)

    slug: str | None = Field(
        pattern=SLUG_PATTERN,
        max_length=100,
        description="URL 友好标识",
    )
