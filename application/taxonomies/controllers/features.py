from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from advanced_alchemy.filters import SearchFilter
from litestar import Controller, Request, Response, get, post
from litestar.datastructures.multi_dicts import FormMultiDict
from litestar.params import FromPath, FromQuery, QueryParameter, URLEncodedBody
from litestar.response import Template
from sqlalchemy import select

from application.contents.enums import PublishStatus
from application.contents.models import Content
from application.contents.schemas import ContentLiteSchema
from application.contents.services import ContentService
from application.guards import PermissionGuard
from application.htmx import HTMXMixin
from application.taxonomies.forms import ContentIdsForm, FeatureDestroyForm, FeatureForm
from application.taxonomies.models import Feature
from application.taxonomies.schemas import FeatureSchema
from application.taxonomies.services import FeatureService
from application.web.cache import invalidate_by_references

group = "推荐管理"
view_permission = PermissionGuard("features:view", "查看推荐", group)
create_permission = PermissionGuard("features:create", "创建推荐", group)
update_permission = PermissionGuard("features:update", "更新推荐", group)
destroy_permission = PermissionGuard("features:destroy", "删除推荐", group)


class FeatureController(HTMXMixin, Controller):
    path = "/features"

    dependencies = {
        "service": create_service_provider(FeatureService),
        "content_service": create_service_provider(ContentService),
    }

    @get(name="features:index", guards=[view_permission])
    async def index(
        self,
        service: FeatureService,
        search: FromQuery[str | None] = None,
        page: Annotated[int, QueryParameter(ge=1)] = 1,
        page_size: Annotated[int, QueryParameter(ge=1, le=100)] = 10,
    ) -> Template:
        filters = []
        if search:
            filters.append(SearchFilter(field_name="name", value=search, ignore_case=True))

        pagination = await service.paginate(
            *filters,
            page=page,
            page_size=page_size,
            order_by=[("created_at", False)],
            schema_type=FeatureSchema,
        )

        return self.htmx_render(
            template_name="features.html.j2",
            context={"pagination": pagination},
        )

    @get("new", name="features:new", guards=[create_permission])
    async def new(self) -> Template:
        return self.htmx_render(
            template_name="feature_form.html.j2",
            context={"form": FeatureForm()},
            block_name=None,
        )

    @get("{item_id:uuid}/edit", name="features:edit", guards=[update_permission])
    async def edit(
        self,
        item_id: FromPath[UUID],
        service: FeatureService,
        request: Request,
    ) -> Template:
        obj = await service.get(item_id)

        return self.htmx_render(
            template_name="feature_form.html.j2",
            context={"form": FeatureForm(obj=obj)},
            block_name=None,
        )

    @post(name="features:create", guards=[create_permission])
    async def create(
        self,
        data: URLEncodedBody[FormMultiDict],
        service: FeatureService,
    ) -> Response | Template:
        form = FeatureForm(formdata=data)
        if form.validate():
            feature = await service.create(form.data)
            # 推荐位无独立前台页面 (无 path), 只删首页 (内置默认)
            await invalidate_by_references(feature)
            return self.htmx_success("添加成功", redirect=data.get("url"))
        return self.htmx_render(
            template_name="feature_form.html.j2",
            context={"form": form},
        )

    @post("{item_id:uuid}", name="features:update", guards=[update_permission])
    async def update(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: FeatureService,
    ) -> Response:
        form = FeatureForm(formdata=data)
        if form.validate():
            feature = await service.update(form.data, item_id)
            # 推荐位无独立前台页面 (无 path), 只删首页 (内置默认)
            await invalidate_by_references(feature)
            return self.htmx_success("更新成功", redirect=data.get("url"))

        return self.htmx_render(
            template_name="feature_form.html.j2",
            context={"form": form},
        )

    @get(
        "{item_id:uuid}/destroy",
        name="features:destroy_form",
        guards=[destroy_permission],
    )
    async def destroy_form(
        self,
        item_id: FromPath[UUID],
        service: FeatureService,
    ) -> Template:
        feature = await service.get(item_id)
        form = FeatureDestroyForm(obj=feature)
        return self.htmx_render(
            template_name="feature_destroy.html.j2",
            context={"form": form},
        )

    @post(
        "{item_id:uuid}/destroy",
        name="features:destroy",
        guards=[destroy_permission],
    )
    async def destroy(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: FeatureService,
    ) -> Response:
        form = FeatureDestroyForm(formdata=data)
        feature = await service.get(item_id)
        if form.validate():
            await service.delete(item_id)
            # 推荐位无独立前台页面 (无 path), 只删首页 (内置默认)
            await invalidate_by_references(feature)
            return self.htmx_success("删除成功")
        return self.htmx_render(
            template_name="feature_destroy.html.j2",
            context={"form": form},
        )

    # ============ 内容管理 ============

    @get(
        "{item_id:uuid}/manage",
        name="features:manage_contents",
        guards=[update_permission],
    )
    async def manage_contents(
        self,
        item_id: FromPath[UUID],
        service: FeatureService,
        content_service: ContentService,
        page: Annotated[int, QueryParameter(ge=1)] = 1,
        page_size: Annotated[int, QueryParameter(ge=1, le=100)] = 10,
    ) -> Template:
        feature = service.to_schema(await service.get(item_id), schema_type=FeatureSchema)
        pagination = await content_service.paginate(
            load=[Content.category, Content.creator],
            statement=select(Content).where(Content.features.any(Feature.id == item_id)),
            page=page,
            page_size=page_size,
            schema_type=ContentLiteSchema,
        )
        return self.htmx_render(
            template_name="feature_manage.html.j2",
            context={"feature": feature, "pagination": pagination},
        )

    @get(
        "{item_id:uuid}/manage/available",
        name="features:manage_available",
        guards=[update_permission],
    )
    async def manage_available(
        self,
        item_id: FromPath[UUID],
        service: FeatureService,
        content_service: ContentService,
        search: FromQuery[str | None] = None,
        page: Annotated[int, QueryParameter(ge=1)] = 1,
        page_size: Annotated[int, QueryParameter(ge=1, le=100)] = 10,
    ) -> Template:
        feature = service.to_schema(await service.get(item_id), schema_type=FeatureSchema)
        statement = select(Content).where(
            Content.status == PublishStatus.PUBLISHED,
            ~Content.features.any(Feature.id == item_id),
        )
        filters = []
        if search:
            filters.append(SearchFilter(field_name="title", value=search, ignore_case=True))
        pagination = await content_service.paginate(
            *filters,
            load=[Content.category, Content.creator],
            statement=statement,
            page=page,
            page_size=page_size,
            schema_type=ContentLiteSchema,
        )
        return self.htmx_render(
            template_name="feature_manage_dialog.html.j2",
            context={
                "feature": feature,
                "pagination": pagination,
                "search": search or "",
            },
            block_name=None,
        )

    @post(
        "{item_id:uuid}/manage/attach",
        name="features:attach_contents",
        guards=[update_permission],
    )
    async def attach_contents(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: FeatureService,
    ) -> Response:
        form = ContentIdsForm(data)
        if form.validate():
            if form.content_ids.data:
                await service.attach_contents(item_id, form.content_ids.data)
            return self.htmx_success("关联成功", redirect=form.url.data)
        return self.htmx_error("内容 ID 格式非法", redirect=form.url.data)

    @post(
        "{item_id:uuid}/manage/detach",
        name="features:detach_contents",
        guards=[update_permission],
    )
    async def detach_contents(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: FeatureService,
    ) -> Response:
        form = ContentIdsForm(data)
        if form.validate():
            if form.content_ids.data:
                await service.detach_contents(item_id, form.content_ids.data)
            return self.htmx_success("移除成功", redirect=form.url.data)
        return self.htmx_error("内容 ID 格式非法", redirect=form.url.data)
