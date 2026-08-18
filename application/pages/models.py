from __future__ import annotations

from urllib.parse import urljoin

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column

from application.settings.manager import get_settings


class Page(UUIDv7AuditBase):
    """
    独立单页模型 (如关于我们 / 联系我们 / 投稿指南)

    与栏目/标签/专题/推荐位没有强关系，走独立的轻量模型。
    `path` 为固定链接 (如 /about)，与 Category / Content 统一在前台 catch-all 解析器
    中精确匹配，不依赖前缀。
    """

    __tablename__ = "contents_pages"
    __table_args__ = (
        # 与 Category 一致：path 必须以 / 开头，保证前台解析器归一化匹配
        CheckConstraint("path LIKE '/%'", name="ck_page_path_prefix"),
    )

    title: Mapped[str] = mapped_column(String(255))
    # 固定链接，存库，前台 catch-all 用 path == full 精确匹配
    path: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500))
    cover_url: Mapped[str | None] = mapped_column(String(255))

    # 单页正文
    text: Mapped[str] = mapped_column(
        Text().with_variant(MEDIUMTEXT, "mysql", "mariadb")
    )

    # 指定渲染模板，默认 page.html，特殊页可单独配 about.html / contact.html
    template: Mapped[str | None] = mapped_column(String(100), comment="模板")

    is_active: Mapped[bool] = mapped_column(
        default=True, index=True, comment="上线状态"
    )

    @property
    def url(self) -> str:
        return self.path

    @property
    def absolute_url(self) -> str:
        return urljoin(get_settings("site_url", ""), self.url)
