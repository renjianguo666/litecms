from __future__ import annotations

from datetime import datetime
from uuid import UUID

from application.schemas import Schema


class SitemapSchema(Schema):
    absolute_url: str
    updated_at: datetime


class PushLogSchema(Schema):
    """推送日志展示层 Schema。"""

    id: UUID
    url: str
    platform: str
    status: str
    response: str | None
    created_at: datetime
