from __future__ import annotations

from uuid import UUID

from advanced_alchemy.exceptions import DuplicateKeyError
from advanced_alchemy.extensions.litestar.providers import create_service_provider
from advanced_alchemy.filters import SearchFilter
from litestar import Controller, Response, get, post
from litestar.datastructures.multi_dicts import FormMultiDict
from litestar.exceptions import ClientException
from litestar.params import FromPath, FromQuery, URLEncodedBody
from litestar.response import Template
from msgspec import convert

from application.checks import PathConflictError
from application.contents.models import Content
from application.contents.services import ContentService
from application.guards import PermissionGuard
from application.htmx import HTMXMixin
from application.taxonomies.cache import invalidate_categories as invalidate
from application.taxonomies.forms import CategoryDestroyForm, CategoryForm
from application.taxonomies.models import Category
from application.taxonomies.schemas import CategorySchema
from application.taxonomies.services import CategoryService

view_permission = PermissionGuard("categories:view", "查看栏目", "栏目管理")
create_permission = PermissionGuard(
    "categories:create", "创建栏目", "栏目管理"
)
update_permission = PermissionGuard(
    "categories:update", "更新栏目", "栏目管理"
)
destroy_permission = PermissionGuard(
    "categories:destroy", "删除栏目", "栏目管理"
)


class CategoryController(HTMXMixin, Controller):
    path = "/categories"

    dependencies = {
        "service": create_service_provider(CategoryService),
        "content_service": create_service_provider(ContentService),
    }

    @get(name="categories:index", guards=[view_permission])
    async def index(
        self,
        service: CategoryService,
        search: FromQuery[str | None] = None,
    ) -> Template:
        if search:
            categories = convert(
                await service.get_many(
                    SearchFilter(field_name="name", value=search, ignore_case=True)
                ),
                list[CategorySchema],
                from_attributes=True,
            )
        else:
            categories = convert(
                await service.get_tree(),
                list[CategorySchema],
                from_attributes=True,
            )

        return self.htmx_render(
            template_name="categories.html.j2",
            context={"categories": categories},
        )

    @get("new", name="categories:new", guards=[create_permission])
    async def new(self, service: CategoryService) -> Template:
        return self.htmx_render(
            template_name="category_form.html.j2",
            context={
                "form": CategoryForm(),
                "category_tree": await service.get_tree(),
            },
        )

    @get("{item_id:uuid}/edit", name="categories:edit", guards=[update_permission])
    async def edit(self, item_id: FromPath[UUID], service: CategoryService) -> Template:
        obj = await service.get(item_id)
        return self.htmx_render(
            template_name="category_form.html.j2",
            context={
                "form": CategoryForm(obj=obj),
                "category": obj,
                "category_tree": await service.get_tree(),
            },
        )

    @post(name="categories:create", guards=[create_permission])
    async def create(
        self,
        data: URLEncodedBody[FormMultiDict],
        service: CategoryService,
    ) -> Response | Template:
        form = CategoryForm(formdata=data)
        if form.validate():
            try:
                await service.create(form.data)
            except PathConflictError as exc:
                form.append_field_error("path", str(exc))
            else:
                await invalidate()
                return self.htmx_success("添加成功", redirect=data.get("url"))
        return self.htmx_render(
            template_name="category_form.html.j2",
            context={"form": form, "category_tree": await service.get_tree()},
        )

    @post("{item_id:uuid}", name="categories:update", guards=[update_permission])
    async def update(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: CategoryService,
    ) -> Response:
        form = CategoryForm(formdata=data)
        if form.validate():
            try:
                await service.update(form.data, item_id)
            except PathConflictError as exc:
                form.append_field_error("path", str(exc))
            except DuplicateKeyError:
                form.append_field_error("path", "该路径已被占用")
            except ClientException as exc:
                form.append_field_error("parent_id", exc.detail)
            else:
                await invalidate()
                return self.htmx_success("更新成功", redirect=data.get("url"))
        return self.htmx_render(
            template_name="category_form.html.j2",
            context={
                "form": form,
                "category_tree": await service.get_tree(),
                "category": await service.get(item_id),
            },
        )

    @get(
        "{item_id:uuid}/destroy",
        name="categories:destroy_form",
        guards=[destroy_permission],
    )
    async def destroy_form(
        self,
        item_id: FromPath[UUID],
        service: CategoryService,
        content_service: ContentService,
    ) -> Template | Response:
        form = CategoryDestroyForm(obj=await service.get(item_id))

        if await service.exists(Category.parent_id == item_id):
            form.form_errors.append("该栏目下还有子栏目，请先删除子栏目")
            form.disabled()

        elif await content_service.exists(Content.category_id == item_id):
            form.form_errors.append("该栏目下内容将被一并删除")
        return self.htmx_render(
            template_name="category_destroy.html.j2",
            context={"form": form},
        )

    @post(
        "{item_id:uuid}/destroy",
        name="categories:destroy",
        guards=[destroy_permission],
    )
    async def destroy(
        self,
        item_id: FromPath[UUID],
        service: CategoryService,
        data: URLEncodedBody[FormMultiDict],
    ) -> Response:
        form = CategoryDestroyForm(data, obj=await service.get(item_id))
        if await service.exists(Category.parent_id == item_id):
            form.form_errors.append("该栏目下还有子栏目，请先删除子栏目")
            form.disabled()
        elif form.validate():
            await service.delete(item_id)
            await invalidate()
            return self.htmx_success("删除成功")
        return self.htmx_render(
            template_name="category_destroy.html.j2",
            context={"form": form},
        )
