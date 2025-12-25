from __future__ import annotations

from datetime import datetime, timezone
from random import randint
from typing import TYPE_CHECKING
from urllib.parse import urljoin
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import Enum as SaEnum
from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from .enums import PublishStatus

if TYPE_CHECKING:
    from application.accounts.models import User
    from application.taxonomies.models import Category, Feature, Special, Tag


class Content(UUIDv7AuditBase):
    """
    内容基类 (Content)
    """

    __tablename__ = "contents_items"

    # --- 1. 多态 (Polymorphic JTI) 设置 ---

    polymorphic_type: Mapped[str] = mapped_column(String(50), index=True)

    __mapper_args__ = {
        "polymorphic_on": polymorphic_type,
        "polymorphic_identity": "content",
    }

    __table_args__ = (
        # 栏目文章列表：按栏目筛选 + 状态筛选 + 发布时间排序
        Index(
            "ix_content_category_status_published",
            "category_id",
            "status",
            "published_at",
        ),
    )

    path: Mapped[str] = mapped_column(String(255), unique=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(String(500))

    cover_url: Mapped[str | None] = mapped_column(String(255))
    source: Mapped[str | None] = mapped_column(String(200))
    author: Mapped[str | None] = mapped_column(String(100))

    creator_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts_users.id", ondelete="RESTRICT"),
        index=True,
    )

    creator: Mapped["User"] = relationship(
        back_populates="contents",
        lazy="joined",
        foreign_keys=[creator_id],
    )

    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("taxonomies_categories.id", ondelete="RESTRICT"),
        index=True,
    )

    category: Mapped["Category"] = relationship(
        back_populates="contents", lazy="joined", foreign_keys=[category_id]
    )

    specials: Mapped[list["Special"]] = relationship(
        secondary="taxonomies_specials_contents",
        back_populates="contents",
        lazy="raise",
    )

    # (关键 M2M) 标签关系
    tags: Mapped[list["Tag"]] = relationship(
        secondary="taxonomies_tags_contents", back_populates="contents", lazy="raise"
    )

    # (关键 M2M) 推荐位关系
    features: Mapped[list["Feature"]] = relationship(
        secondary="taxonomies_features_contents",
        back_populates="contents",
        lazy="raise",
    )

    status: Mapped[PublishStatus] = mapped_column(
        SaEnum(PublishStatus, native_enum=False),
        default=PublishStatus.DRAFT,
        index=True,
    )
    views: Mapped[int] = mapped_column(default=lambda: randint(10000, 99999))

    published_at: Mapped[datetime | None] = mapped_column(
        DateTimeUTC(timezone=True), index=True
    )

    @property
    def is_published(self) -> bool:
        return (
            self.status == PublishStatus.PUBLISHED
            and self.published_at is not None
            and self.published_at <= datetime.now(timezone.utc)
        )

    @property
    def is_draft(self) -> bool:
        return self.status == PublishStatus.DRAFT

    @property
    def is_archived(self) -> bool:
        return self.status == PublishStatus.ARCHIVED

    @hybrid_property
    def creator_username(self) -> str:
        """创建者用户名（用于列表展示）"""
        return self.creator.username if self.creator else ""

    @hybrid_property
    def category_name(self) -> str:
        """分类名称（用于列表展示）"""
        return self.category.name if self.category else ""

    @property
    def url(self) -> str:
        if self.category.domain:
            segments = self.path.split("/")
            return urljoin(self.category.domain, "/".join(segments[2:]))
        return self.path


# 简单的单词转复数
def pluralize(name: str) -> str:
    # "S/X/Z/CH/SH" 规则
    # e.g., "box" -> "boxes"
    # e.g., "bus" -> "buses"
    # e.g., "search" -> "searches"
    if name.endswith(("s", "x", "z")) or name.endswith(("ch", "sh")):
        return name + "es"

    # "Y 结尾" 规则
    if name.endswith("y"):
        # 检查 'y' 前面一个字母
        if len(name) > 1 and name[-2:-1].lower() in "aeiou":
            # 2a. "元音" + y (e.g., 'key', 'day') -> 'keys', 'days'
            return name + "s"
        else:
            # 2b. "辅音" + y (e.g., 'category') -> 'categories'
            return name[:-1] + "ies"

    return name + "s"


class ContentBase(Content):
    """
    内容类型的抽象基类 (Abstract Base for Content Types)
    """

    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"contents_{pluralize(cls.__name__.lower())}"

    @declared_attr.directive
    def __mapper_args__(cls):
        return {"polymorphic_identity": cls.__name__.lower()}

    @declared_attr
    def id(cls) -> Mapped[UUID]:  # type: ignore
        return mapped_column(
            ForeignKey("contents_items.id", ondelete="CASCADE"),
            primary_key=True,
        )
