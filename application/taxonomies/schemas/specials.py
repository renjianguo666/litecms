from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from application.web.urls import build_special_url

Name = Annotated[str, Field(min_length=1, max_length=100, description="专题名称")]

SpecialSlug = Annotated[
    str,
    Field(
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=100, description="专题标识"
    ),
]

Title = Annotated[str, Field(min_length=1, max_length=255, description="专题标题")]
Description = Annotated[str, Field(max_length=500, description="专题描述")]
CoverUrl = Annotated[str, Field(max_length=255, description="封面图片URL")]
IsActive = Annotated[bool, Field(description="上线状态")]
Priority = Annotated[int, Field(description="排序优先级")]
PublishedAt = Annotated[datetime, Field(description="发布时间")]


class SpecialLiteSchema(BaseModel):
    """专题简要信息（用于文章详情展示）"""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    name: str
    slug: str
    title: str
    description: str | None = None
    cover_url: str | None = None
    is_active: bool
    priority: int
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def url(self) -> str:
        return build_special_url(self.slug)


class SpecialSchema(SpecialLiteSchema):
    pass


class SpecialCreateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: Name
    slug: SpecialSlug
    title: Title

    description: Description | None = None
    cover_url: CoverUrl | None = None

    is_active: IsActive = False
    priority: Priority = 0
    published_at: PublishedAt | None = None


class SpecialUpdateSchema(BaseModel):
    """更新专题"""

    model_config = ConfigDict(frozen=True)

    name: Name | None = None
    slug: SpecialSlug | None = None
    title: Title | None = None
    description: Description | None = None
    cover_url: CoverUrl | None = None
    is_active: IsActive | None = None
    priority: Priority | None = None
    published_at: PublishedAt | None = None
