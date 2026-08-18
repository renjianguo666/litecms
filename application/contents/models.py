from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional
from urllib.parse import urljoin
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from advanced_alchemy.types import DateTimeUTC
from sqlalchemy import Enum as SaEnum
from sqlalchemy import ForeignKey, Index, String, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from application.config import cfg
from application.settings.manager import get_settings

from .enums import PublishStatus

if TYPE_CHECKING:
    from application.accounts.models import User
    from application.taxonomies.models import (
        Category,
        Feature,
        Special,
        Tag,
    )


class Content(UUIDv7AuditBase):
    __tablename__ = "contents_items"
    __table_args__ = (
        Index(
            "ix_content_category_status_published",
            "category_id",
            "status",
            "published_at",
        ),
    )
    __mapper_args__ = {
        "polymorphic_on": "polymorphic_type",
        "polymorphic_identity": "content",
    }

    polymorphic_type: Mapped[str] = mapped_column(String(50), index=True)
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
        lazy="raise",
        foreign_keys=[creator_id],
    )

    category_id: Mapped[UUID] = mapped_column(
        ForeignKey("taxonomies_categories.id", ondelete="RESTRICT"),
        index=True,
    )

    category: Mapped["Category"] = relationship(
        back_populates="contents", lazy="raise", foreign_keys=[category_id]
    )

    tags: Mapped[list["Tag"]] = relationship(
        secondary="taxonomies_tags_contents",
        passive_deletes=True,
        back_populates="contents",
        lazy="raise",
    )

    specials: Mapped[list["Special"]] = relationship(
        secondary="taxonomies_specials_contents",
        passive_deletes=True,
        back_populates="contents",
        lazy="raise",
    )

    features: Mapped[list["Feature"]] = relationship(
        secondary="taxonomies_features_contents",
        passive_deletes=True,
        back_populates="contents",
        lazy="raise",
    )

    status: Mapped[PublishStatus] = mapped_column(
        SaEnum(PublishStatus, native_enum=False),
        default=PublishStatus.DRAFT,
        index=True,
    )
    views: Mapped[int] = mapped_column(default=0)

    published_at: Mapped[datetime] = mapped_column(
        DateTimeUTC(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    @validates("published_at")
    def validate_published_at(self, _: str, value: datetime) -> datetime:
        if value.tzinfo is None:
            value = value.replace(tzinfo=cfg.tzinfo)
        return value.astimezone(timezone.utc)

    @hybrid_property
    def creator_username(self) -> str:
        return self.creator.username if self.creator else ""

    @creator_username.expression
    def expression_creator_username(cls):
        return (
            select(User.username)
            .where(User.id == cls.creator_id)
            .correlate(Content)
            .scalar_subquery()
        )

    @hybrid_property
    def category_name(self) -> str:
        return self.category.name if self.category else ""

    @category_name.expression
    def expression_category_name(cls):
        return (
            select(Category.name)
            .where(Category.id == cls.category_id)
            .correlate(Content)
            .scalar_subquery()
        )

    @property
    def url(self) -> str:
        if self.category.domain:
            return "/".join(self.path.split("/")[2:])
        return self.path

    @property
    def absolute_url(self) -> str:
        if self.category.domain:
            return urljoin(self.category.domain, self.url)
        return urljoin(get_settings("site_url", ""), self.url)

    def to_dict(self, exclude: Optional[set[str]] = None) -> dict[str, Any]:
        return {**super().to_dict(exclude=exclude or set()), "url": self.url}
