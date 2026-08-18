from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.base import AdvancedDeclarativeBase, UUIDv7AuditBase
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from application.contents.models import Content


class Feature(UUIDv7AuditBase):
    """
    Feature (推荐位/分发渠道)

    name: 中文显示名 "首页头条" (后台/前台展示用)
    slug: 英文程序标识 "headline" (代码/模板引用, 唯一, 改名不影响代码)
    """

    __tablename__ = "taxonomies_features"

    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)

    # M2M 关系: Feature <-> Content
    contents: Mapped[list["Content"]] = relationship(
        secondary="taxonomies_features_contents",
        passive_deletes=True,
        back_populates="features",
        lazy="raise",
    )


class FeatureContent(AdvancedDeclarativeBase):
    """
    M2M 关联表: Content <-> Feature
    """

    __tablename__ = "taxonomies_features_contents"

    content_id: Mapped[UUID] = mapped_column(
        ForeignKey("contents_items.id", ondelete="CASCADE"),
        primary_key=True,
    )
    feature_id: Mapped[UUID] = mapped_column(
        ForeignKey("taxonomies_features.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    # === 排序 ===
    priority: Mapped[int] = mapped_column(default=0, comment="优先级(值越大越靠前)")

    # === 关系 ===
    content: Mapped["Content"] = relationship(
        lazy="raise", overlaps="contents,features"
    )
    feature: Mapped["Feature"] = relationship(
        lazy="raise", overlaps="contents,features"
    )
