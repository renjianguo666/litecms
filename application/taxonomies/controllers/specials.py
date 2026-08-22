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
from application.taxonomies.forms import ContentIdsForm, SpecialDestroyForm, SpecialForm
from application.taxonomies.models import Special
from application.taxonomies.schemas import SpecialSchema
from application.taxonomies.services import SpecialService

view_permission = PermissionGuard("specials:view", "查看专题", "专题管理")
create_permission = PermissionGuard("specials:create", "创建专题", "专题管理")
update_permission = PermissionGuard("specials:update", "更新专题", "专题管理")
destroy_permission = PermissionGuard(
    "specials:destroy", "删除专题", "专题管理"
)


class SpecialController(HTMXMixin, Controller):
    path = "/specials"

    dependencies = {
        "service": create_service_provider(SpecialService),
        "content_service": create_service_provider(ContentService),
    }

    @get(name="specials:index", guards=[view_permission])
    async def index(
        self,
        service: SpecialService,
        search: FromQuery[str | None] = None,
        page: Annotated[int, QueryParameter(ge=1)] = 1,
        page_size: Annotated[int, QueryParameter(ge=1, le=100)] = 10,
    ) -> Template:
        filters = []
        if search:
            filters.append(
                SearchFilter(field_name="name", value=search, ignore_case=True)
            )

        pagination = await service.paginate(
            *filters,
            page=page,
            page_size=page_size,
            order_by=[("created_at", False)],
            schema_type=SpecialSchema,
        )

        return self.htmx_render(
            template_name="specials.html.j2",
            context={"pagination": pagination},
        )

    @get("new", name="specials:new", guards=[create_permission])
    async def new(self) -> Template:
        return self.htmx_render(
            template_name="special_form.html.j2",
            context={"form": SpecialForm()},
        )

    @get("{item_id:uuid}/edit", name="specials:edit", guards=[update_permission])
    async def edit(
        self,
        item_id: FromPath[UUID],
        service: SpecialService,
        request: Request,
    ) -> Template:
        obj = await service.get(item_id)

        return self.htmx_render(
            template_name="special_form.html.j2",
            context={"form": SpecialForm(obj=obj)},
        )

    @post(name="specials:create", guards=[create_permission])
    async def create(
        self,
        data: URLEncodedBody[FormMultiDict],
        service: SpecialService,
    ) -> Response | Template:
        form = SpecialForm(formdata=data)
        if form.validate():
            await service.create(form.data)
            return self.htmx_success("添加成功", redirect=data.get("url"))
        return self.htmx_render(
            template_name="special_form.html.j2",
            context={"form": form},
        )

    @post("{item_id:uuid}", name="specials:update", guards=[update_permission])
    async def update(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: SpecialService,
    ) -> Response:
        form = SpecialForm(formdata=data)
        if form.validate():
            await service.update(form.data, item_id)
            return self.htmx_success("更新成功", redirect=data.get("url"))

        return self.htmx_render(
            template_name="special_form.html.j2",
            context={"form": form},
        )

    @get(
        "{item_id:uuid}/destroy",
        name="specials:destroy_form",
        guards=[destroy_permission],
    )
    async def destroy_form(
        self,
        item_id: FromPath[UUID],
        service: SpecialService,
    ) -> Template:
        special = await service.get(item_id)
        form = SpecialDestroyForm(obj=special)
        return self.htmx_render(
            template_name="special_destroy.html.j2",
            context={"form": form},
        )

    @post(
        "{item_id:uuid}/destroy",
        name="specials:destroy",
        guards=[destroy_permission],
    )
    async def destroy(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: SpecialService,
    ) -> Response:
        form = SpecialDestroyForm(formdata=data)
        if form.validate():
            await service.delete(item_id)
            return self.htmx_success("删除成功")
        return self.htmx_render(
            template_name="special_destroy.html.j2",
            context={"form": form},
        )

    # ============ 内容管理 ============

    @get(
        "{item_id:uuid}/manage",
        name="specials:manage_contents",
        guards=[update_permission],
    )
    async def manage_contents(
        self,
        item_id: FromPath[UUID],
        service: SpecialService,
        content_service: ContentService,
        page: Annotated[int, QueryParameter(ge=1)] = 1,
        page_size: Annotated[int, QueryParameter(ge=1, le=100)] = 10,
    ) -> Template:
        special = service.to_schema(
            await service.get(item_id), schema_type=SpecialSchema
        )
        pagination = await content_service.paginate(
            load=[Content.category, Content.creator],
            statement=select(Content).where(
                Content.specials.any(Special.id == item_id)
            ),
            page=page,
            page_size=page_size,
            schema_type=ContentLiteSchema,
        )
        return self.htmx_render(
            template_name="special_manage.html.j2",
            context={"special": special, "pagination": pagination},
        )

    @get(
        "{item_id:uuid}/manage/available",
        name="specials:manage_available",
        guards=[update_permission],
    )
    async def manage_available(
        self,
        item_id: FromPath[UUID],
        service: SpecialService,
        content_service: ContentService,
        search: FromQuery[str | None] = None,
        page: Annotated[int, QueryParameter(ge=1)] = 1,
        page_size: Annotated[int, QueryParameter(ge=1, le=100)] = 10,
    ) -> Template:
        special = service.to_schema(
            await service.get(item_id), schema_type=SpecialSchema
        )
        statement = select(Content).where(
            Content.status == PublishStatus.PUBLISHED,
            ~Content.specials.any(Special.id == item_id),
        )
        filters = []
        if search:
            filters.append(
                SearchFilter(field_name="title", value=search, ignore_case=True)
            )
        pagination = await content_service.paginate(
            *filters,
            load=[Content.category, Content.creator],
            statement=statement,
            page=page,
            page_size=page_size,
            schema_type=ContentLiteSchema,
        )
        return self.htmx_render(
            template_name="special_manage_dialog.html.j2",
            context={
                "special": special,
                "pagination": pagination,
                "search": search or "",
            },
            block_name=None,
        )

    @post(
        "{item_id:uuid}/manage/attach",
        name="specials:attach_contents",
        guards=[update_permission],
    )
    async def attach_contents(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: SpecialService,
    ) -> Response:
        form = ContentIdsForm(data)
        if form.validate():
            if form.content_ids.data:
                await service.attach_contents(item_id, form.content_ids.data)
            return self.htmx_success("关联成功", redirect=form.url.data)
        return self.htmx_error("内容 ID 格式非法", redirect=form.url.data)

    @post(
        "{item_id:uuid}/manage/detach",
        name="specials:detach_contents",
        guards=[update_permission],
    )
    async def detach_contents(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: SpecialService,
    ) -> Response:
        form = ContentIdsForm(data)
        if form.validate():
            if form.content_ids.data:
                await service.detach_contents(item_id, form.content_ids.data)
            return self.htmx_success("移除成功", redirect=form.url.data)
        return self.htmx_error("内容 ID 格式非法", redirect=form.url.data)
