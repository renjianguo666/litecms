"""前台 Schema 组装层。

设计原则: 各业务模块持有自己的 XxxSchema / XxxLiteSchema
(articles/schemas.py、taxonomies/schemas.py、pages/schemas.py、
contents/schemas.py、accounts/schemas.py), 本模块只做两件事:
1. re-export 各模块 schema, 供前台控制器/模板标签直接引用;
2. 定义 web 特有的展示组合 (如栏目树 CategorySchema = Lite + children 递归)。

不在此重复定义业务字段 —— 需要扩展时, 用 class 继承对应模块的 Schema 加字段。
"""

from __future__ import annotations

from msgspec import field as msgspec_field

from application.accounts.schemas import UserLiteSchema
from application.articles.schemas import ArticleLiteSchema, ArticleSchema
from application.contents.schemas import ContentLiteSchema, ContentSchema
from application.pages.schemas import PageSchema
from application.schemas import Schema
from application.taxonomies.schemas import (
    CategoryLiteSchema,
    FeatureSchema,
    SpecialSchema,
    TagSchema,
)

__all__ = [
    "ArticleLiteSchema",
    "ArticleSchema",
    "CategoryLiteSchema",
    "CategorySchema",
    "ContentLiteSchema",
    "ContentSchema",
    "FeatureSchema",
    "PageSchema",
    "SpecialSchema",
    "TagSchema",
    "UserLiteSchema",
    "BreadcrumbSchema",
]


class CategorySchema(CategoryLiteSchema):
    """前台栏目树: 轻量版 + children 递归 (web 特有组装)。"""

    children: list[CategorySchema] = msgspec_field(default_factory=list)


class BreadcrumbSchema(Schema):
    """面包屑节点: 取自栏目祖先链 (Category.id.in_(trail.split(".")))。"""

    name: str
    url: str
