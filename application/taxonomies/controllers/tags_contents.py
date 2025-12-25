from __future__ import annotations

from uuid import UUID

import sqlalchemy as sa
from litestar import Controller, delete, get, post
from litestar.exceptions import NotFoundException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from application.guards import PermissionGuard

from ..models import Tag, TagContent
from ..schemas import (
    PushContentsResponseSchema,
    PushContentsSchema,
    TagContentsResponse,
    TagContentItem,
)

view_permission = PermissionGuard("taxonomies:view_tag_content", "查看标签内容")
manage_permission = PermissionGuard("taxonomies:manage_tag_content", "管理标签内容")


class TagContentController(Controller):
    path = "/tags/{tag_id:uuid}/contents"
    tags = ["Taxonomy (标签内容)"]

    @get(guards=[view_permission])
    async def list_contents(
        self,
        tag_id: UUID,
        db_session: AsyncSession,
    ) -> TagContentsResponse:
        """获取标签下的内容列表"""

        # 查询标签
        tag = await db_session.get(Tag, tag_id)
        if tag is None:
            raise NotFoundException("标签不存在")

        # 查询标签内内容
        stmt = (
            sa.select(TagContent)
            .where(TagContent.tag_id == tag_id)
            .options(joinedload(TagContent.content))
        )
        result = await db_session.execute(stmt)
        items = result.scalars().all()

        return TagContentsResponse(
            tag_id=tag.id,
            name=tag.name,
            slug=tag.slug,
            contents=[
                TagContentItem(
                    content_id=item.content_id,
                    title=item.content.title,
                )
                for item in items
            ],
        )

    @post(guards=[manage_permission])
    async def push_contents(
        self,
        tag_id: UUID,
        data: PushContentsSchema,
        db_session: AsyncSession,
    ) -> PushContentsResponseSchema:
        """批量添加内容到标签"""
        # 验证标签是否存在
        tag = await db_session.get(Tag, tag_id)
        if tag is None:
            raise NotFoundException("标签不存在")

        # 查询已存在的关联
        existing_stmt = sa.select(TagContent.content_id).where(
            TagContent.tag_id == tag_id,
            TagContent.content_id.in_(data.content_ids),
        )
        result = await db_session.execute(existing_stmt)
        existing_ids = set(result.scalars().all())

        # 只添加不存在的
        added = 0
        for content_id in data.content_ids:
            if content_id not in existing_ids:
                tag_content = TagContent(
                    tag_id=tag_id,
                    content_id=content_id,
                )
                db_session.add(tag_content)
                added += 1

        if added > 0:
            await db_session.commit()

        return PushContentsResponseSchema(
            added=added, total_requested=len(data.content_ids)
        )

    @delete("/{content_id:uuid}", guards=[manage_permission])
    async def remove_content(
        self,
        tag_id: UUID,
        content_id: UUID,
        db_session: AsyncSession,
    ) -> None:
        """从标签移除内容"""
        # 先查询是否存在
        stmt = sa.select(TagContent).where(
            TagContent.tag_id == tag_id,
            TagContent.content_id == content_id,
        )
        result = await db_session.execute(stmt)
        tag_content = result.scalar_one_or_none()

        if tag_content is None:
            raise NotFoundException("内容不在该标签中")

        await db_session.delete(tag_content)
        await db_session.commit()
