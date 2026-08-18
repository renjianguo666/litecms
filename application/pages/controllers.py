from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from advanced_alchemy.filters import SearchFilter
from litestar import Controller, Response, get, post
from litestar.datastructures.multi_dicts import FormMultiDict
from litestar.params import FromPath, FromQuery, QueryParameter, URLEncodedBody
from litestar.response import Template

from application.checks import PathConflictError
from application.guards import PermissionGuard
from application.htmx import HTMXMixin
from application.pages.forms import PageDestroyForm
from application.pages.schemas import PageSchema

from .forms import PageForm
from .services import PageService

view_permission = PermissionGuard("pages:view", "查看单页", "单页管理")
create_permission = PermissionGuard("pages:create", "创建单页", "单页管理")
update_permission = PermissionGuard("pages:update", "更新单页", "单页管理")
destroy_permission = PermissionGuard("pages:destroy", "删除单页", "单页管理")


class PageController(HTMXMixin, Controller):
    path = "/pages"

    dependencies = {
        "service": create_service_provider(PageService),
    }

    @get("/tiptap", name="pages:tiptap")
    async def tiptap(self) -> Template:
        return self.htmx_render(
            template_name="tiptap.html.j2",
        )

    @get(name="pages:index", guards=[view_permission])
    async def index(
        self,
        service: PageService,
        search: FromQuery[str | None] = None,
        page: Annotated[int, QueryParameter(ge=1)] = 1,
        page_size: Annotated[int, QueryParameter(ge=1, le=100)] = 10,
    ) -> Template:
        filters = []
        if search:
            filters.append(
                SearchFilter(field_name="title", value=search, ignore_case=True)
            )

        pagination = await service.paginate(
            *filters,
            page=page,
            page_size=page_size,
            order_by=[("created_at", True)],
            schema_type=PageSchema,
        )

        return self.htmx_render(
            template_name="pages.html.j2",
            context={"pagination": pagination},
        )

    @get("new", name="pages:new", guards=[create_permission])
    async def new(self) -> Template:
        form = PageForm()
        return self.htmx_render(
            template_name="page_form.html.j2",
            context={"form": form},
        )

    @get("{item_id:uuid}/edit", name="pages:edit", guards=[update_permission])
    async def edit(
        self,
        item_id: FromPath[UUID],
        service: PageService,
    ) -> Template:
        obj = await service.get(item_id)
        return self.htmx_render(
            template_name="page_form.html.j2",
            context={"form": PageForm(obj=obj)},
        )

    @post(name="pages:create", guards=[create_permission])
    async def create(
        self,
        service: PageService,
        data: URLEncodedBody[FormMultiDict],
    ) -> Response | Template:
        form = PageForm(formdata=data)
        if form.validate():
            try:
                await service.create(form.data)
            except PathConflictError as exc:
                form.append_field_error("path", str(exc))
                return self.htmx_render(
                    template_name="page_form.html.j2",
                    context={"form": form},
                )
            return self.htmx_success("添加成功", redirect=data.get("url"))
        return self.htmx_render(
            template_name="page_form.html.j2",
            context={"form": form},
        )

    @post("{item_id:uuid}", name="pages:update", guards=[update_permission])
    async def update(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: PageService,
    ) -> Response | Template:
        form = PageForm(formdata=data)
        if form.validate():
            try:
                await service.update(form.data, item_id)
            except PathConflictError as exc:
                form.append_field_error("path", str(exc))
                return self.htmx_render(
                    template_name="page_form.html.j2",
                    context={"form": form},
                )
            return self.htmx_success("更新成功", redirect=data.get("url"))

        return self.htmx_render(
            template_name="page_form.html.j2",
            context={"form": form},
        )

    @get(
        "{item_id:uuid}/destroy",
        name="pages:destroy_form",
        guards=[destroy_permission],
    )
    async def destroy_form(
        self,
        item_id: FromPath[UUID],
        service: PageService,
    ) -> Template:
        page = await service.get(item_id)
        form = PageDestroyForm(obj=page)
        return self.htmx_render(
            template_name="page_destroy.html.j2",
            context={"form": form},
        )

    @post(
        "{item_id:uuid}/destroy",
        name="pages:destroy",
        guards=[destroy_permission],
    )
    async def destroy(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: PageService,
    ) -> Response:
        form = PageDestroyForm(formdata=data)
        if form.validate():
            await service.delete(item_id)
            return self.htmx_success("删除成功")
        return self.htmx_render(
            template_name="page_destroy.html.j2",
            context={"form": form},
        )
