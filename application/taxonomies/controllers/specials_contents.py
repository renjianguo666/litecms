from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import sqlalchemy as sa
from litestar import Controller, delete, get, patch, post
from litestar.exceptions import NotFoundException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from application.guards import PermissionGuard

from ..models import Special, SpecialContent
from ..schemas import (
    PushContentsResponseSchema,
    PushContentsSchema,
    SortContentsResponseSchema,
    SortContentsSchema,
    SpecialContentsResponse,
    SpecialContentItem,
)

view_permission = PermissionGuard("taxonomies:view_special_content", "查看专题内容")
manage_permission = PermissionGuard("taxonomies:manage_special_content", "管理专题内容")


class SpecialContentController(Controller):
    path = "/specials/{special_id:uuid}/contents"
    tags = ["Taxonomy (专题内容)"]

    @get(guards=[view_permission])
    async def list_contents(
        self,
        special_id: UUID,
        db_session: AsyncSession,
    ) -> SpecialContentsResponse:
        """获取专题下的内容列表"""

        # 查询专题
        special = await db_session.get(Special, special_id)
        if special is None:
            raise NotFoundException("专题不存在")

        # 查询专题内内容
        stmt = (
            sa.select(SpecialContent)
            .where(SpecialContent.special_id == special_id)
            .options(joinedload(SpecialContent.content))
            .order_by(SpecialContent.position, SpecialContent.added_at.desc())
        )
        result = await db_session.execute(stmt)
        items = result.scalars().all()

        return SpecialContentsResponse(
            special_id=special.id,
            name=special.name,
            slug=special.slug,
            title=special.title,
            description=special.description,
            cover_url=special.cover_url,
            contents=[
                SpecialContentItem(
                    content_id=item.content_id,
                    position=item.position,
                    headline=item.headline,
                    added_at=item.added_at,
                    title=item.content.title,
                )
                for item in items
            ],
        )

    @post(guards=[manage_permission])
    async def push_contents(
        self,
        special_id: UUID,
        data: PushContentsSchema,
        db_session: AsyncSession,
    ) -> PushContentsResponseSchema:
        """批量添加内容到专题"""
        # 验证专题是否存在
        special = await db_session.get(Special, special_id)
        if special is None:
            raise NotFoundException("专题不存在")

        # 查询已存在的关联
        existing_stmt = sa.select(SpecialContent.content_id).where(
            SpecialContent.special_id == special_id,
            SpecialContent.content_id.in_(data.content_ids),
        )
        result = await db_session.execute(existing_stmt)
        existing_ids = set(result.scalars().all())

        # 获取当前最大 position
        max_pos_stmt = sa.select(
            sa.func.coalesce(sa.func.max(SpecialContent.position), -1)
        ).where(SpecialContent.special_id == special_id)
        max_position = await db_session.scalar(max_pos_stmt) or -1

        # 只添加不存在的
        added = 0
        for content_id in data.content_ids:
            if content_id not in existing_ids:
                max_position += 1
                special_content = SpecialContent(
                    special_id=special_id,
                    content_id=content_id,
                    position=max_position,
                    headline=False,
                    added_at=datetime.now(timezone.utc),
                )
                db_session.add(special_content)
                added += 1

        if added > 0:
            await db_session.commit()

        return PushContentsResponseSchema(
            added=added, total_requested=len(data.content_ids)
        )

    @delete("/{content_id:uuid}", guards=[manage_permission])
    async def remove_content(
        self,
        special_id: UUID,
        content_id: UUID,
        db_session: AsyncSession,
    ) -> None:
        """从专题移除内容"""
        # 先查询是否存在
        stmt = sa.select(SpecialContent).where(
            SpecialContent.special_id == special_id,
            SpecialContent.content_id == content_id,
        )
        result = await db_session.execute(stmt)
        special_content = result.scalar_one_or_none()

        if special_content is None:
            raise NotFoundException("内容不在该专题中")

        await db_session.delete(special_content)
        await db_session.commit()

    @patch("/sort", guards=[manage_permission])
    async def sort_contents(
        self,
        special_id: UUID,
        data: SortContentsSchema,
        db_session: AsyncSession,
    ) -> SortContentsResponseSchema:
        """批量调整专题内内容顺序"""
        if not data.items:
            return SortContentsResponseSchema(updated=0)

        # 验证所有内容都在专题中
        content_ids = [item.content_id for item in data.items]
        existing_stmt = sa.select(SpecialContent.content_id).where(
            SpecialContent.special_id == special_id,
            SpecialContent.content_id.in_(content_ids),
        )
        result = await db_session.execute(existing_stmt)
        existing_ids = set(result.scalars().all())

        missing = set(content_ids) - existing_ids
        if missing:
            raise NotFoundException(f"部分内容不在该专题中: {missing}")

        # 使用 CASE WHEN 批量更新 position（单条 SQL）
        case_stmt = sa.case(
            *[
                (SpecialContent.content_id == item.content_id, item.position)
                for item in data.items
            ],
            else_=SpecialContent.position,
        )
        stmt = (
            sa.update(SpecialContent)
            .where(
                SpecialContent.special_id == special_id,
                SpecialContent.content_id.in_(content_ids),
            )
            .values(position=case_stmt)
        )
        await db_session.execute(stmt)
        await db_session.commit()

        return SortContentsResponseSchema(updated=len(data.items))
