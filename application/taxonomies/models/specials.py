from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.base import AdvancedDeclarativeBase, UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from application.contents.models import Content


class Special(UUIDv7AuditBase):
    """专题模型"""

    __tablename__ = "taxonomies_specials"

    name: Mapped[str] = mapped_column(String(255), index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(500))
    cover_url: Mapped[str | None] = mapped_column(String(255))

    # === 状态与排序 ===
    is_active: Mapped[bool] = mapped_column(
        default=True, index=True, comment="上线状态"
    )
    priority: Mapped[int] = mapped_column(default=0, comment="排序优先级")
    published_at: Mapped[datetime | None] = mapped_column(
        DateTimeUTC(timezone=True), index=True, comment="发布时间"
    )

    # === 关系 ===
    contents: Mapped[list["Content"]] = relationship(
        secondary="taxonomies_specials_contents",
        back_populates="specials",
        lazy="raise",
    )

    @property
    def url(self) -> str:
        return self.slug


class SpecialContent(AdvancedDeclarativeBase):
    """专题-内容 关联表（用于单独操作中间表数据）"""

    __tablename__ = "taxonomies_specials_contents"

    content_id: Mapped[UUID] = mapped_column(
        ForeignKey("contents_items.id", ondelete="CASCADE"),
        primary_key=True,
    )
    special_id: Mapped[UUID] = mapped_column(
        ForeignKey("taxonomies_specials.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,  # 反向索引：查询某专题的所有文章
    )

    # === 专题内排序 ===
    position: Mapped[int] = mapped_column(default=0, comment="排序位置(值越小越靠前)")

    # === 头条标记 ===
    headline: Mapped[bool] = mapped_column(
        default=False, index=True, comment="是否为专题头条"
    )

    # === 添加时间 ===
    added_at: Mapped[datetime] = mapped_column(
        DateTimeUTC(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="添加到专题的时间",
    )

    # === 关系 ===
    content: Mapped["Content"] = relationship(
        lazy="raise", overlaps="contents,specials"
    )
    special: Mapped["Special"] = relationship(
        lazy="raise", overlaps="contents,specials"
    )
