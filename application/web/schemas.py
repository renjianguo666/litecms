"""前台只读 Schema 层。

与后台管理用 Schema (application/taxonomies/schemas.py 等) 区分:
后台暴露管理字段 (parent_id/trail/priority/is_active/created_at...),
前台只需模板直出所需的轻量字段, 且文章详情需要嵌套 category/creator
等关系转成的子 Schema (后台 ContentSchema 为规避 lazy="raise" 用
category_name/creator_username 字符串, 前台详情页则需结构化对象)。

ORM -> Schema 统一走 msgspec.convert(obj, Schema, from_attributes=True),
datetime/可空字段的归一由 Schema.__post_init__ 自动完成, 模板侧无需判断。
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from msgspec import field as msgspec_field

from application.schemas import Schema


class UserSchema(Schema):
    """文章作者(创建者)展示信息。"""

    id: UUID
    username: str
    alias: str


class CategoryLiteSchema(Schema):
    """栏目轻量信息, 作为文章内嵌的所属栏目 / 栏目树节点。"""

    id: UUID
    name: str
    title: str | None
    description: str | None
    cover_url: str | None
    url: str
    absolute_url: str
    page_size: int
    parent_id: UUID | None
    path: str
    content_path: str
    template: str | None
    priority: int


class CategorySchema(CategoryLiteSchema):
    children: list[CategorySchema] = msgspec_field(default_factory=list)


class SpecialSchema(Schema):
    """专题展示信息。"""

    id: UUID
    name: str
    title: str
    description: str | None
    slug: str
    cover_url: str | None
    url: str
    template: str | None


class FeatureSchema(Schema):
    """推荐位展示信息。"""

    id: UUID
    name: str
    slug: str


class TagSchema(Schema):
    """标签展示信息。"""

    id: UUID
    name: str
    slug: str
    url: str


class PageSchema(Schema):
    """单页展示信息。"""

    id: UUID
    title: str
    path: str
    url: str
    description: str | None
    cover_url: str | None
    text: str
    template: str | None


class ArticleLiteSchema(Schema):
    """文章列表项: 栏目页/标签页/专题页分页用。

    category/creator 为关系字段, 查询时必须 eager load (joinedload),
    否则 lazy="raise" 会抛 MissingGreenlet。
    """

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
    category: CategoryLiteSchema
    creator: UserSchema


class ArticleSchema(ArticleLiteSchema):
    """文章详情: 在列表项基础上补正文与关联集合。

    tags/specials/features 同样需查询时 selectinload。
    """

    text: str
    tags: list[TagSchema]
    specials: list[SpecialSchema]
    features: list[FeatureSchema]


class BreadcrumbSchema(Schema):
    """面包屑节点: 取自栏目祖先链 (Category.id.in_(trail.split(".")))。"""

    name: str
    url: str
