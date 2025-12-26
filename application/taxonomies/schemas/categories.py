from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

PATH_DESC = "可用占位符{key}{year}{month}{day}{y}{m}{d}"
PATH_CONTENT_DESC = "可用占位符{key}{year}{month}{day}{y}{m}{d}{parent}"

PATH = Annotated[
    str, Field(min_length=1, description=PATH_DESC, examples=["/category/{key}"])
]
CONTENT_PATH = Annotated[
    str,
    Field(
        min_length=1,
        description=PATH_CONTENT_DESC,
        examples=["/{category}/{year}/{key}.html"],
    ),
]
NAME = Annotated[str, Field(min_length=1, max_length=100, description="栏目名称")]
TITLE = Annotated[str, Field(max_length=200)]
DESCRIPTION = Annotated[str, Field(max_length=500)]
COVER_URL = Annotated[str, Field(max_length=255)]
PRIORITY = Annotated[int, Field(description="优先级排序")]
TEMPLATE = Annotated[str, Field(min_length=1, max_length=255, description="模板")]
PAGE_SIZE = Annotated[int, Field(ge=1, le=100, description="每页条数")]
DOMAIN = Annotated[str, Field(max_length=100)]


class CategoryLiteSchema(BaseModel):
    """栏目简要信息"""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    parent_id: UUID | None = None
    depth: int
    name: str
    title: str | None = None
    description: str | None = None
    cover_url: str | None = None
    url: str
    page_size: int
    priority: int
    template: str | None
    created_at: datetime
    updated_at: datetime | None = None

    path: PATH
    content_path: CONTENT_PATH
    domain: DOMAIN | None = None


class CategorySchema(CategoryLiteSchema):
    parent: CategoryLiteSchema | None = None


class CategoryCreateSchema(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: NAME
    path: PATH
    content_path: CONTENT_PATH
    template: TEMPLATE | None = None

    # 可选字段 (默认为 None)
    title: TITLE | None = None
    description: DESCRIPTION | None = None
    cover_url: COVER_URL | None = None
    page_size: PAGE_SIZE | None = 15
    priority: PRIORITY | None = None
    parent_id: UUID | None = None

    domain: DOMAIN | None = None


class CategoryUpdateSchema(BaseModel):
    """更新栏目"""

    model_config = ConfigDict(frozen=True)

    name: NAME | None = None
    path: PATH | None = None
    content_path: CONTENT_PATH | None = None
    title: TITLE | None = None
    description: DESCRIPTION | None = None
    cover_url: COVER_URL | None = None
    page_size: PAGE_SIZE | None = None
    priority: PRIORITY | None = None
    template: TEMPLATE | None = None
    parent_id: UUID | None = None

    domain: DOMAIN | None = None
