from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urljoin
from uuid import UUID

from advanced_alchemy.base import AdvancedDeclarativeBase, UUIDv7AuditBase
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from application.settings.manager import get_settings

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
    # 模板(与 Category.template 对齐: 专题可选指定前台展示模板)
    template: Mapped[str | None] = mapped_column(String(100), comment="模板")

    # === 状态与排序 ===
    is_active: Mapped[bool] = mapped_column(
        default=True, index=True, comment="上线状态"
    )
    priority: Mapped[int] = mapped_column(default=0, comment="排序优先级")

    # === 关系 ===
    contents: Mapped[list[Content]] = relationship(
        secondary="taxonomies_specials_contents",
        passive_deletes=True,
        back_populates="specials",
        lazy="raise",
    )

    @property
    def url(self) -> str:
        return self.slug

    @property
    def absolute_url(self) -> str:
        return urljoin(get_settings("site_url", ""), self.url)


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
    priority: Mapped[int] = mapped_column(default=0, comment="优先级(值越大越靠前)")

    # === 关系 ===
    content: Mapped[Content] = relationship(
        lazy="raise", overlaps="contents,specials"
    )
    special: Mapped[Special] = relationship(
        lazy="raise", overlaps="contents,specials"
    )
