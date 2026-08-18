from __future__ import annotations

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class PushLog(UUIDv7AuditBase):
    """SEO 推送日志"""

    __tablename__ = "seo_push_logs"

    url: Mapped[str] = mapped_column(String(500), index=True)
    platform: Mapped[str] = mapped_column(String(20), comment="推送平台: baidu")
    status: Mapped[str] = mapped_column(String(20), comment="推送结果: success/failed")
    response: Mapped[str | None] = mapped_column(
        String(1000), comment="搜索引擎返回内容"
    )
