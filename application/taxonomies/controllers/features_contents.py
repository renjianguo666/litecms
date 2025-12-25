from __future__ import annotations

from uuid import UUID

import sqlalchemy as sa
from litestar import Controller, delete, get, post
from litestar.exceptions import NotFoundException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from application.guards import PermissionGuard

from ..models import Feature, FeatureContent
from ..schemas import (
    FeatureContentsResponse,
    FeatureContentItem,
    PushContentsResponseSchema,
    PushContentsSchema,
)

view_permission = PermissionGuard("taxonomies:view_feature_content", "查看推荐位内容")
manage_permission = PermissionGuard(
    "taxonomies:manage_feature_content", "管理推荐位内容"
)


class FeatureContentController(Controller):
    path = "/features/{feature_id:uuid}/contents"
    tags = ["Taxonomy (推荐位内容)"]

    @get(guards=[view_permission])
    async def list_contents(
        self,
        feature_id: UUID,
        db_session: AsyncSession,
    ) -> FeatureContentsResponse:
        """获取推荐位下的内容列表"""

        # 查询推荐位
        feature = await db_session.get(Feature, feature_id)
        if feature is None:
            raise NotFoundException("推荐位不存在")

        # 查询推荐位内内容
        stmt = (
            sa.select(FeatureContent)
            .where(FeatureContent.feature_id == feature_id)
            .options(joinedload(FeatureContent.content))
        )
        result = await db_session.execute(stmt)
        items = result.scalars().all()

        return FeatureContentsResponse(
            feature_id=feature.id,
            name=feature.name,
            contents=[
                FeatureContentItem(
                    content_id=item.content_id,
                    title=item.content.title,
                )
                for item in items
            ],
        )

    @post(guards=[manage_permission])
    async def push_contents(
        self,
        feature_id: UUID,
        data: PushContentsSchema,
        db_session: AsyncSession,
    ) -> PushContentsResponseSchema:
        """批量添加内容到推荐位"""
        # 验证推荐位是否存在
        feature = await db_session.get(Feature, feature_id)
        if feature is None:
            raise NotFoundException("推荐位不存在")

        # 查询已存在的关联
        existing_stmt = sa.select(FeatureContent.content_id).where(
            FeatureContent.feature_id == feature_id,
            FeatureContent.content_id.in_(data.content_ids),
        )
        result = await db_session.execute(existing_stmt)
        existing_ids = set(result.scalars().all())

        # 只添加不存在的
        added = 0
        for content_id in data.content_ids:
            if content_id not in existing_ids:
                feature_content = FeatureContent(
                    feature_id=feature_id,
                    content_id=content_id,
                )
                db_session.add(feature_content)
                added += 1

        if added > 0:
            await db_session.commit()

        return PushContentsResponseSchema(
            added=added, total_requested=len(data.content_ids)
        )

    @delete("/{content_id:uuid}", guards=[manage_permission])
    async def remove_content(
        self,
        feature_id: UUID,
        content_id: UUID,
        db_session: AsyncSession,
    ) -> None:
        """从推荐位移除内容"""
        # 先查询是否存在
        stmt = sa.select(FeatureContent).where(
            FeatureContent.feature_id == feature_id,
            FeatureContent.content_id == content_id,
        )
        result = await db_session.execute(stmt)
        feature_content = result.scalar_one_or_none()

        if feature_content is None:
            raise NotFoundException("内容不在该推荐位中")

        await db_session.delete(feature_content)
        await db_session.commit()
