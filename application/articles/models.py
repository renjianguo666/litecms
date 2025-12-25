from __future__ import annotations

from sqlalchemy import Text
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column

# (关键) 导入您的 Content 基类
from application.contents.models import ContentBase, PublishStatus

__all__ = [
    "Article",
    "PublishStatus",
]


class Article(ContentBase):
    """
    Article (文章) 模型
    """

    text: Mapped[str] = mapped_column(
        Text().with_variant(MEDIUMTEXT, "mysql", "mariadb")
    )
