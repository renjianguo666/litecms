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
from application.contents.schemas import ContentSchema
from application.contents.services import ContentService
from application.guards import PermissionGuard
from application.htmx import HTMXMixin
from application.taxonomies.forms import ContentIdsForm, TagDestroyForm, TagForm
from application.taxonomies.models import Tag
from application.taxonomies.schemas import TagSchema
from application.taxonomies.services import TagService

view_permission = PermissionGuard("tags:view", "查看标签", "标签管理")
create_permission = PermissionGuard("tags:create", "创建标签", "标签管理")
update_permission = PermissionGuard("tags:update", "更新标签", "标签管理")
destroy_permission = PermissionGuard("tags:destroy", "删除标签", "标签管理")


class TagController(HTMXMixin, Controller):
    path = "/tags"

    dependencies = {
        "service": create_service_provider(TagService),
        "content_service": create_service_provider(ContentService),
    }

    # ============ CRUD ============

    @get(name="tags:index", guards=[view_permission])
    async def index(
        self,
        service: TagService,
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
            schema_type=TagSchema,
        )
        return self.htmx_render(
            template_name="tags.html.j2",
            context={"pagination": pagination},
        )

    @get("new", name="tags:new", guards=[create_permission])
    async def new(self) -> Template:
        return self.htmx_render(
            template_name="tag_form.html.j2",
            context={"form": TagForm()},
            block_name=None,
        )

    @get("{item_id:uuid}/edit", name="tags:edit", guards=[update_permission])
    async def edit(
        self,
        item_id: FromPath[UUID],
        service: TagService,
        request: Request,
    ) -> Template:
        obj = await service.get(item_id)
        return self.htmx_render(
            template_name="tag_form.html.j2",
            context={"form": TagForm(obj=obj)},
            block_name=None,
        )

    @post(name="tags:create", guards=[create_permission])
    async def create(
        self,
        data: URLEncodedBody[FormMultiDict],
        service: TagService,
    ) -> Response | Template:
        form = TagForm(formdata=data)
        if form.validate():
            await service.create(form.data)
            return self.htmx_success("添加成功", redirect=data.get("url"))
        return self.htmx_render(
            template_name="tag_form.html.j2",
            context={"form": form},
        )

    @post("{item_id:uuid}", name="tags:update", guards=[update_permission])
    async def update(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: TagService,
    ) -> Response:
        form = TagForm(formdata=data)
        if form.validate():
            await service.update(form.data, item_id)
            return self.htmx_success("更新成功", redirect=data.get("url"))
        return self.htmx_render(
            template_name="tag_form.html.j2",
            context={"form": form},
        )

    @get(
        "{item_id:uuid}/destroy",
        name="tags:destroy_form",
        guards=[destroy_permission],
    )
    async def destroy_form(
        self,
        item_id: FromPath[UUID],
        service: TagService,
    ) -> Template:
        tag = await service.get(item_id)
        form = TagDestroyForm(obj=tag)
        return self.htmx_render(
            template_name="tag_destroy.html.j2",
            context={"form": form},
        )

    @post(
        "{item_id:uuid}/destroy",
        name="tags:destroy",
        guards=[destroy_permission],
    )
    async def destroy(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: TagService,
    ) -> Response:
        form = TagDestroyForm(formdata=data)
        if form.validate():
            await service.delete(item_id)
            return self.htmx_success("删除成功")
        return self.htmx_render(
            template_name="tag_destroy.html.j2",
            context={"form": form},
        )

    # ============ 内容管理 ============

    @get(
        "{item_id:uuid}/manage", name="tags:manage_contents", guards=[update_permission]
    )
    async def manage_contents(
        self,
        item_id: FromPath[UUID],
        service: TagService,
        content_service: ContentService,
        page: Annotated[int, QueryParameter(ge=1)] = 1,
        page_size: Annotated[int, QueryParameter(ge=1, le=100)] = 10,
    ) -> Template:
        tag = service.to_schema(await service.get(item_id), schema_type=TagSchema)
        pagination = await content_service.paginate(
            load=[Content.category, Content.creator],
            statement=select(Content).where(Content.tags.any(Tag.id == item_id)),
            page=page,
            page_size=page_size,
            schema_type=ContentSchema,
        )
        return self.htmx_render(
            template_name="tag_manage.html.j2",
            context={"tag": tag, "pagination": pagination},
        )

    @get(
        "{item_id:uuid}/manage/available",
        name="tags:manage_available",
        guards=[update_permission],
    )
    async def manage_available(
        self,
        item_id: FromPath[UUID],
        service: TagService,
        content_service: ContentService,
        search: FromQuery[str | None] = None,
        page: Annotated[int, QueryParameter(ge=1)] = 1,
        page_size: Annotated[int, QueryParameter(ge=1, le=100)] = 10,
    ) -> Template:
        tag = service.to_schema(await service.get(item_id), schema_type=TagSchema)
        statement = select(Content).where(
            Content.status == PublishStatus.PUBLISHED,
            ~Content.tags.any(Tag.id == item_id),
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
            schema_type=ContentSchema,
        )
        return self.htmx_render(
            template_name="tag_manage_dialog.html.j2",
            context={"tag": tag, "pagination": pagination, "search": search or ""},
            block_name=None,
        )

    @post(
        "{item_id:uuid}/manage/attach",
        name="tags:attach_contents",
        guards=[update_permission],
    )
    async def attach_contents(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: TagService,
    ) -> Response:
        form = ContentIdsForm(data)
        if form.validate():
            if form.content_ids.data:
                await service.attach_contents(item_id, form.content_ids.data)
            return self.htmx_success("关联成功", redirect=form.url.data)
        return self.htmx_error("内容 ID 格式非法", redirect=form.url.data)

    @post(
        "{item_id:uuid}/manage/detach",
        name="tags:detach_contents",
        guards=[update_permission],
    )
    async def detach_contents(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: TagService,
    ) -> Response:
        form = ContentIdsForm(data)
        if form.validate():
            if form.content_ids.data:
                await service.detach_contents(item_id, form.content_ids.data)
            return self.htmx_success("移除成功", redirect=form.url.data)
        return self.htmx_error("内容 ID 格式非法", redirect=form.url.data)
