from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.filters import LimitOffset, SearchFilter
from advanced_alchemy.service import OffsetPagination
from litestar import Controller, Request, delete, get, patch, post
from litestar.params import Parameter
from sqlalchemy.orm import lazyload

from application.deps import create_service_provider
from application.guards import PermissionGuard

from ..schemas import (
    FeatureCreateSchema,
    FeatureSchema,
    FeatureUpdateSchema,
)
from ..services import FeatureService

view_permission = PermissionGuard("taxonomies:view_feature", "查看推荐位")
create_permission = PermissionGuard("taxonomies:create_feature", "创建推荐位")
update_permission = PermissionGuard("taxonomies:update_feature", "更新推荐位")
delete_permission = PermissionGuard("taxonomies:delete_feature", "删除推荐位")


class FeatureController(Controller):
    path = "/features"
    tags = ["Taxonomy (推荐位)"]

    dependencies = {"service": create_service_provider(FeatureService)}

    @get(guards=[view_permission])
    async def list_features(
        self,
        service: FeatureService,
        limit_offset: LimitOffset,
        search: Annotated[str | None, Parameter(default=None)],
    ) -> OffsetPagination[FeatureSchema]:
        filters = []
        if search:
            filters.append(
                SearchFilter(field_name="name", value=search, ignore_case=True)
            )

        filters.append(limit_offset)

        results, total = await service.list_and_count(*filters, load=lazyload("*"))
        return service.to_schema(
            data=results, total=total, schema_type=FeatureSchema, filters=filters
        )

    @get("{item_id:uuid}", guards=[view_permission])
    async def get_feature(
        self, item_id: UUID, service: FeatureService
    ) -> FeatureSchema:
        feature = await service.get(item_id)
        return service.to_schema(data=feature, schema_type=FeatureSchema)

    @post(guards=[create_permission])
    async def create_feature(
        self, service: FeatureService, data: FeatureCreateSchema, request: Request
    ) -> FeatureSchema:
        feature = await service.create(data)
        request.app.emit("feature_changed")
        return service.to_schema(data=feature, schema_type=FeatureSchema)

    @patch("{item_id:uuid}", guards=[update_permission])
    async def update_feature(
        self,
        item_id: UUID,
        service: FeatureService,
        data: FeatureUpdateSchema,
        request: Request,
    ) -> FeatureSchema:
        feature = await service.update(data, item_id)
        request.app.emit("feature_changed")
        return service.to_schema(data=feature, schema_type=FeatureSchema)

    @delete("{item_id:uuid}", guards=[delete_permission])
    async def delete_feature(
        self, item_id: UUID, service: FeatureService, request: Request
    ) -> None:
        await service.delete(item_id)
        request.app.emit("feature_changed")
