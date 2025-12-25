from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.base import AdvancedDeclarativeBase, UUIDv7AuditBase
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from application.contents.models import Content


class Tag(UUIDv7AuditBase):
    """
    Tag (标签) 模型
    """

    __tablename__ = "taxonomies_tags"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)

    # (关键 M2M) "contents" 关系
    contents: Mapped[list["Content"]] = relationship(
        secondary="taxonomies_tags_contents",
        back_populates="tags",
        lazy="selectin",
    )

    @property
    def url(self) -> str:
        return self.slug


class TagContent(AdvancedDeclarativeBase):
    """
    M2M 关联表: Content <-> Tag
    """

    __tablename__ = "taxonomies_tags_contents"

    content_id: Mapped[UUID] = mapped_column(
        ForeignKey("contents_items.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[UUID] = mapped_column(
        ForeignKey("taxonomies_tags.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,  # 反向索引：查询某标签的所有文章
    )

    # === 关系 ===
    content: Mapped["Content"] = relationship(lazy="raise", overlaps="contents,tags")
    tag: Mapped["Tag"] = relationship(lazy="raise", overlaps="contents,tags")
