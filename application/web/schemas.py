from __future__ import annotations

import datetime
import uuid

from pydantic import BaseModel, ConfigDict, TypeAdapter


class User(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: uuid.UUID
    email: str
    username: str


class CategoryLite(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: uuid.UUID
    name: str
    title: str | None = None
    description: str | None = None
    cover_url: str | None = None
    url: str
    page_size: int


class Category(CategoryLite):
    """
    继承自 CategoryLite，目前字段一致。
    如果有额外字段（比如 parent/children），可以在这里添加。
    """

    pass


class Special(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: uuid.UUID
    name: str
    title: str
    description: str | None = None
    slug: str
    cover_url: str | None = None
    published_at: datetime.datetime | None = None


class Feature(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: uuid.UUID
    name: str


class Tag(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str


class ArticleLite(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: uuid.UUID
    url: str
    title: str
    views: int
    cover_url: str | None = None
    source: str | None = None
    author: str | None = None
    description: str | None = None
    published_at: datetime.datetime | None = None

    # 嵌套模型
    category: CategoryLite
    creator: User


class Article(ArticleLite):
    """
    文章详情，包含完整的关联信息
    """

    text: str
    specials: list[Special]
    features: list[Feature]
    tags: list[Tag]


class Breadcrumb(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    name: str
    url: str


article_list_adapter = TypeAdapter(list[ArticleLite])
breadcrumb_list_adapter = TypeAdapter(list[Breadcrumb])
category_list_adapter = TypeAdapter(list[CategoryLite])
feature_list_adapter = TypeAdapter(list[Feature])
tag_list_adapter = TypeAdapter(list[Tag])
special_list_adapter = TypeAdapter(list[Special])
