from __future__ import annotations

import platform
import sys

import psutil
from advanced_alchemy.extensions.litestar.providers import create_service_provider
from advanced_alchemy.filters import LimitOffset, OrderBy
from litestar import Controller, get
from litestar.response import Template
from msgspec import convert
from sqlalchemy.ext.asyncio import AsyncSession

from application.contents.models import Content
from application.contents.schemas import ContentLiteSchema
from application.contents.services import ContentService
from application.guards import PermissionGuard
from application.htmx import HTMXMixin

SYS_OS = platform.system()
SYS_PYTHON = sys.version.split()[0]
TARGET_PATH = "/" if SYS_OS != "Windows" else "C:\\"

view_permission = PermissionGuard("dashboard:view", "查看仪表盘", "仪表盘")


def _get_sys_info(db_session: AsyncSession) -> dict:
    try:
        database = db_session.get_bind().dialect.name.capitalize()
    except AttributeError:
        database = "Unknown"

    try:
        disk = psutil.disk_usage(TARGET_PATH)
        disk_free = f"{round(disk.free / (1024**3), 1)} GB"
        disk_total = f"{round(disk.total / (1024**3), 1)} GB"
        disk_percent = round(disk.percent)
    except OSError:
        disk_free = disk_total = "未知"
        disk_percent = 0

    mem = psutil.virtual_memory()

    return {
        "os": SYS_OS,
        "python": SYS_PYTHON,
        "database": database,
        "disk_free": disk_free,
        "disk_total": disk_total,
        "disk_percent": disk_percent,
        "mem_total": f"{round(mem.total / (1024**3), 1)} GB",
        "mem_used": f"{round(mem.used / (1024**3), 1)} GB",
        "mem_percent": round(mem.percent),
    }


class DashboardController(HTMXMixin, Controller):
    path = "/"

    dependencies = {
        "content_service": create_service_provider(ContentService),
    }

    @get(name="dashboard:index", guards=[view_permission])
    async def index(
        self,
        db_session: AsyncSession,
        content_service: ContentService,
    ) -> Template:
        info = _get_sys_info(db_session)

        recent_articles = await content_service.get_many(
            LimitOffset(limit=10, offset=0),
            OrderBy(field_name="published_at", sort_order="desc"),
            load=[Content.category, Content.creator],
        )

        return self.htmx_render(
            template_name="index.html.j2",
            context={
                "sys": info,
                "recent_articles": convert(recent_articles, list[ContentLiteSchema], from_attributes=True),
            },
        )
