from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column

from application.contents.models import Content

__all__ = ["Article"]


class Article(Content):
    """
    Article (文章) 模型
    """

    __tablename__ = "contents_articles"
    __mapper_args__ = {"polymorphic_identity": "article"}

    id: Mapped[UUID] = mapped_column(ForeignKey(Content.id), primary_key=True)

    text: Mapped[str] = mapped_column(
        Text().with_variant(MEDIUMTEXT, "mysql", "mariadb")
    )
