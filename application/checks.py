"""跨表 path 唯一性校验"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.contents.models import Content
from application.pages.models import Page
from application.taxonomies.models.categories import Category


class PathConflictError(ValueError):
    """跨表 path 唯一性冲突"""


_PATH_MODELS = {
    Page: "单页",
    Category: "栏目",
    Content: "内容",
}


async def check_path_unique(
    db_session: AsyncSession,
    path: str,
    *,
    exclude_id: UUID | None = None,
) -> None:
    """跨表校验 path 唯一性 (Page / Category / Content)"""
    for model, label in _PATH_MODELS.items():
        stmt = select(model.id).where(model.path == path)
        hit = await db_session.scalar(stmt)
        if hit is not None and hit != exclude_id:
            raise PathConflictError(f"路径 {path} 已被{label}占用")
