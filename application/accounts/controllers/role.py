from __future__ import annotations

from itertools import groupby
from operator import attrgetter
from typing import Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from advanced_alchemy.filters import SearchFilter
from litestar import Controller, Response, get, post
from litestar.datastructures.multi_dicts import FormMultiDict
from litestar.params import FromPath, FromQuery, QueryParameter, URLEncodedBody
from litestar.response import Template
from sqlalchemy.orm import selectinload

from application.accounts.forms import RoleDestroyForm, RoleForm
from application.accounts.models import Role
from application.accounts.schemas import RoleSchema
from application.accounts.services import PermissionService, RoleService
from application.guards import PermissionGuard
from application.htmx import HTMXMixin

view_permission = PermissionGuard("roles:view", "查看角色", "角色管理")
create_permission = PermissionGuard("roles:create", "创建角色", "角色管理")
update_permission = PermissionGuard("roles:update", "更新角色", "角色管理")
destroy_permission = PermissionGuard("roles:destroy", "删除角色", "角色管理")

GROUP_ORDER = [
    "仪表盘",
    "文章管理",
    "栏目管理",
    "标签管理",
    "专题管理",
    "推荐管理",
    "单页管理",
    "模板管理",
    "用户管理",
    "角色管理",
    "系统设置",
]
ACTION_ORDER = ["view", "create", "update", "destroy"]


def action_index(code: str) -> int:
    """提取权限 code 的 action 后缀，返回在 ACTION_ORDER 中的位置，未列出放最后"""
    action = code.split(":")[-1].split("_")[-1]
    return ACTION_ORDER.index(action) if action in ACTION_ORDER else len(ACTION_ORDER)


def ordered_permission_groups(permissions):
    """按 GROUP_ORDER 分组排序，组内按 ACTION_ORDER 排操作，返回 [(group, [perm, ...]), ...]

    未列入 GROUP_ORDER 的新分组排在已知分组之后, 按 group 名字典序稳定排列
    (否则多个新分组顺序依赖数据库返回顺序, 不稳定)。
    """
    sorted_perms = sorted(
        permissions,
        key=lambda p: (
            (0, GROUP_ORDER.index(p.group)) if p.group in GROUP_ORDER else (1, p.group),
            action_index(p.code),
        ),
    )
    return [
        (group, list(perms))
        for group, perms in groupby(sorted_perms, key=attrgetter("group"))
    ]


class RoleController(HTMXMixin, Controller):
    path = "/roles"
    dependencies = {
        "service": create_service_provider(RoleService),
        "perm_service": create_service_provider(PermissionService),
    }

    @get(name="roles:index", guards=[view_permission])
    async def index(
        self,
        service: RoleService,
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
            order_by=[("name", True)],
            schema_type=RoleSchema,
        )
        return self.htmx_render(
            template_name="roles.html.j2",
            context={"pagination": pagination},
        )

    @get("new", name="roles:new", guards=[create_permission])
    async def new(self, perm_service: PermissionService) -> Template:
        permissions = await perm_service.get_many(order_by=[("code", True)])
        form = RoleForm()
        form.permissions.choices = [(str(p.id), p.name) for p in permissions]
        return self.htmx_render(
            template_name="role_form.html.j2",
            context={
                "form": form,
                "permissions": ordered_permission_groups(permissions),
            },
        )

    @post(name="roles:create", guards=[create_permission])
    async def create(
        self,
        data: URLEncodedBody[FormMultiDict],
        service: RoleService,
        perm_service: PermissionService,
    ) -> Response | Template:
        permissions = await perm_service.get_many(order_by=[("code", True)])
        form = RoleForm(data)
        form.permissions.choices = [(str(p.id), p.name) for p in permissions]
        if form.validate():
            await service.create(form.data)
            return self.htmx_success("添加成功", redirect=data.get("url"))
        return self.htmx_render(
            template_name="role_form.html.j2",
            context={
                "form": form,
                "permissions": ordered_permission_groups(permissions),
            },
        )

    @get(
        "{item_id:uuid}/edit",
        name="roles:edit",
        guards=[update_permission],
    )
    async def edit(
        self,
        item_id: FromPath[UUID],
        service: RoleService,
        perm_service: PermissionService,
    ) -> Template:
        role = await service.get(item_id, load=[selectinload(Role.permissions)])
        permissions = await perm_service.get_many(order_by=[("code", True)])
        form = RoleForm(obj=role)
        form.permissions.choices = [(str(p.id), p.name) for p in permissions]
        form.permissions.data = [str(p.id) for p in role.permissions]
        return self.htmx_render(
            template_name="role_form.html.j2",
            context={
                "form": form,
                "permissions": ordered_permission_groups(permissions),
            },
        )

    @post(
        "{item_id:uuid}",
        name="roles:update",
        guards=[update_permission],
    )
    async def update(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: RoleService,
        perm_service: PermissionService,
    ) -> Response | Template:
        permissions = await perm_service.get_many(order_by=[("code", True)])
        form = RoleForm(formdata=data)
        form.permissions.choices = [(str(p.id), p.name) for p in permissions]
        if form.validate():
            await service.update(
                form.data, item_id, load=[selectinload(Role.permissions)]
            )
            return self.htmx_success("更新成功", redirect=data.get("url"))
        return self.htmx_render(
            template_name="role_form.html.j2",
            context={
                "form": form,
                "permissions": ordered_permission_groups(permissions),
            },
        )

    @get(
        "{item_id:uuid}/destroy",
        name="roles:destroy_form",
        guards=[destroy_permission],
    )
    async def destroy_form(
        self,
        item_id: FromPath[UUID],
        service: RoleService,
    ) -> Template:
        role = await service.get(item_id)
        form = RoleDestroyForm(obj=role)
        return self.htmx_render(
            template_name="role_destroy.html.j2",
            context={"form": form},
        )

    @post(
        "{item_id:uuid}/destroy",
        name="roles:destroy",
        guards=[destroy_permission],
    )
    async def destroy(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: RoleService,
    ) -> Response:
        form = RoleDestroyForm(formdata=data)
        if form.validate():
            await service.delete(item_id)
            return self.htmx_success("删除成功")
        return self.htmx_render(
            template_name="role_destroy.html.j2",
            context={"form": form},
        )
