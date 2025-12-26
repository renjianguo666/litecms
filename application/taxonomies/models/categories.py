from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urljoin
from uuid import UUID

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from application.contents.models import Content


class Category(UUIDv7AuditBase):
    __tablename__ = "taxonomies_categories"
    __table_args__ = (
        # 2. 性能补丁 (PostgreSQL 专用):
        # 标准 Unique 索引对 = 查找很快，但对 LIKE 'abc%' 有时不够快（取决于 locale）。
        # 显式加一个 varchar_pattern_ops 索引，让前缀查询(查找子栏目)快到极致。
        Index(
            "ix_category_trail_pattern",
            "trail",
            postgresql_ops={"trail": "varchar_pattern_ops"},
        ),
        CheckConstraint("path LIKE '/%'", name="ck_category_path_prefix"),
    )

    name: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str | None] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(String(500))
    cover_url: Mapped[str | None] = mapped_column(String(255))

    # 固定链接，必须以/开头，如/news
    path: Mapped[str] = mapped_column(String(255), unique=True)
    # 内容固定链接的格式
    content_path: Mapped[str] = mapped_column(String(255))

    page_size: Mapped[int] = mapped_column(default=20, comment="每页条数")
    # 寻根问祖 保存层级str类型的uuid， 如 uuid.uuid.uuid
    trail: Mapped[str] = mapped_column(String(255), unique=True)
    # 值越大 越优先
    priority: Mapped[int] = mapped_column(default=0, index=True, comment="优先级排序")
    # 模板
    template: Mapped[str | None] = mapped_column(String(100), comment="模板")
    domain: Mapped[str | None] = mapped_column(String(100))

    # 1. 自引用外键
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("taxonomies_categories.id", ondelete="RESTRICT"),
        index=True,
    )

    parent: Mapped["Category"] = relationship(
        remote_side=lambda: Category.id,  # 明确指定远程 ID
        back_populates="children",
        lazy="joined",
        uselist=False,
    )

    children: Mapped[list["Category"]] = relationship(
        back_populates="parent", lazy="selectin"
    )

    contents: Mapped[list[Content]] = relationship(
        back_populates="category", lazy="raise"
    )

    @property
    def depth(self) -> int:
        """栏目深度"""
        return len(self.trail.split(".")) - 1

    @property
    def url(self) -> str:
        if self.domain:
            segments = self.path.split("/")
            return urljoin(self.domain, "/".join(segments[2:]))
        return self.path
