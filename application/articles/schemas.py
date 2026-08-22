from __future__ import annotations

from application.contents.schemas import ContentLiteSchema, ContentSchema


class ArticleLiteSchema(ContentLiteSchema):
    """文章列表项（继承 ContentLiteSchema, 含 category/creator 嵌套）。"""


class ArticleSchema(ContentSchema):
    """文章详情: 继承 ContentSchema（含关系/集合）, 补正文。"""

    text: str
