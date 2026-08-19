from __future__ import annotations

from typing import Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from advanced_alchemy.filters import SearchFilter
from litestar import Controller, Response, get, post
from litestar.datastructures.multi_dicts import FormMultiDict
from litestar.params import FromPath, FromQuery, QueryParameter, URLEncodedBody
from litestar.response import Template
from sqlalchemy.orm import selectinload

from application.accounts.forms import UserCreateForm, UserDestroyForm, UserEditForm
from application.accounts.models import User
from application.accounts.schemas import UserSchema
from application.accounts.services import RoleService, UserService
from application.contents.models import Content
from application.contents.services import ContentService
from application.guards import PermissionGuard
from application.htmx import HTMXMixin

view_permission = PermissionGuard("users:view", "查看用户", "用户管理")
create_permission = PermissionGuard("users:create", "创建用户", "用户管理")
update_permission = PermissionGuard("users:update", "更新用户", "用户管理")
destroy_permission = PermissionGuard("users:destroy", "删除用户", "用户管理")


class UserController(HTMXMixin, Controller):
    path = "/users"

    dependencies = {
        "service": create_service_provider(UserService),
        "role_service": create_service_provider(RoleService),
        "content_service": create_service_provider(ContentService),
    }

    @get(name="users:index", guards=[view_permission])
    async def index(
        self,
        service: UserService,
        search: FromQuery[str | None] = None,
        page: Annotated[int, QueryParameter(ge=1)] = 1,
        page_size: Annotated[int, QueryParameter(ge=1, le=100)] = 10,
    ) -> Template:
        filters = []
        if search:
            filters.append(SearchFilter(field_name="username", value=search, ignore_case=True))
        pagination = await service.paginate(
            *filters,
            load=[selectinload(User.roles)],
            page=page,
            page_size=page_size,
            order_by=[("created_at", False)],
            schema_type=UserSchema,
        )
        return self.htmx_render(
            template_name="users.html.j2",
            context={"pagination": pagination},
        )

    @get("new", name="users:new", guards=[create_permission])
    async def new(self, role_service: RoleService, current_user: User) -> Template:
        form = UserCreateForm()
        form.roles.choices = [(str(r.id), r.name) for r in await role_service.get_many()]
        # 角色分配收归超管(帝国式): 非超管不能给用户分配角色——否则能制造
        # 比自己权限还高的账号, 形成提权路径。与 edit/destroy「非超管不碰超管」
        # 同一套逻辑。非超管只改用户基本信息(密码/启停), 角色由超管配。
        if not current_user.is_superuser:
            del form.roles
        return self.htmx_render(template_name="user_form.html.j2", context={"form": form})

    @get(
        "{item_id:uuid}/edit",
        name="users:edit",
        guards=[update_permission],
    )
    async def edit(
        self,
        item_id: FromPath[UUID],
        service: UserService,
        role_service: RoleService,
        current_user: User,
    ) -> Template | Response:
        user = await service.get(item_id, load=[selectinload(User.roles)])
        # 非超管不得编辑超管(防重置超管密码等提权)
        if user.is_superuser and not current_user.is_superuser:
            return self.htmx_error("无权编辑超级管理员")
        form = UserEditForm(obj=user)
        form.roles.choices = [(str(r.id), r.name) for r in await role_service.get_many()]
        form.roles.data = [str(r.id) for r in user.roles]
        # 角色分配收归超管: 非超管不渲染角色字段。超管不受限。
        if not current_user.is_superuser:
            del form.roles
        return self.htmx_render(template_name="user_form.html.j2", context={"form": form})

    @post(name="users:create", guards=[create_permission])
    async def create(
        self,
        data: URLEncodedBody[FormMultiDict],
        service: UserService,
        role_service: RoleService,
        current_user: User,
    ) -> Response | Template:
        form = UserCreateForm(data)
        form.roles.choices = [(str(r.id), r.name) for r in await role_service.get_many()]
        # 角色分配收归超管: 非超管提交时忽略 roles(防绕过——手动 POST roles 也无效),
        # 创建无角色用户, 由超管事后配角色。超管不受限。
        if not current_user.is_superuser:
            del form.roles
        if form.validate():
            await service.create(form.data)
            return self.htmx_success("添加成功", redirect=data.get("url"))
        return self.htmx_render(template_name="user_form.html.j2", context={"form": form})

    @post(
        "{item_id:uuid}",
        name="users:update",
        guards=[update_permission],
    )
    async def update(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: UserService,
        role_service: RoleService,
        current_user: User,
    ) -> Response:
        # 非超管不得编辑超管(防重置超管密码等提权)
        target = await service.get(item_id)
        if target.is_superuser and not current_user.is_superuser:
            return self.htmx_error("无权编辑超级管理员")
        form = UserEditForm(data)
        form.roles.choices = [(str(r.id), r.name) for r in await role_service.get_many()]
        # 角色分配收归超管: 非超管提交时忽略 roles(防绕过——手动 POST roles 也无效),
        # 保留目标原角色不更新。超管不受限。
        if not current_user.is_superuser:
            del form.roles
        if form.validate():
            form_data = dict(form.data)
            if not form_data.get("password_hash"):
                form_data.pop("password_hash", None)
            # 禁止把自己禁用(否则立即锁出且无法登回), 与 destroy 禁删自己对称
            if current_user.id == item_id and form_data.get("is_active") is False:
                return self.htmx_error("不能禁用自己", redirect=data.get("url"))
            await service.update(form_data, item_id, load=selectinload(User.roles))
            return self.htmx_success("更新成功", redirect=data.get("url"))
        return self.htmx_render(template_name="user_form.html.j2", context={"form": form})

    @get(
        "{item_id:uuid}/destroy",
        name="users:destroy_form",
        guards=[destroy_permission],
    )
    async def destroy_form(
        self,
        item_id: FromPath[UUID],
        service: UserService,
        content_service: ContentService,
        current_user: User,
    ) -> Template:
        target = await service.get(item_id)
        form = UserDestroyForm(obj=target)
        if current_user.id == item_id:
            form.form_errors.append("不能删除自己")
            form.disabled()
        elif target.is_superuser and not current_user.is_superuser:
            form.form_errors.append("无权删除超级管理员")
            form.disabled()
        elif await content_service.exists(Content.creator_id == item_id):
            form.form_errors.append("此用户的内容将被一并删除")
            form.form_errors.append("如需保留内容，建议禁用此用户")
        return self.htmx_render(
            template_name="user_destroy.html.j2",
            context={"form": form},
        )

    @post(
        "{item_id:uuid}/destroy",
        name="users:destroy",
        status_code=200,
        guards=[destroy_permission],
    )
    async def destroy(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: UserService,
        content_service: ContentService,
        current_user: User,
    ) -> Response:
        form = UserDestroyForm(data)
        target = await service.get(item_id)
        if current_user.id == item_id:
            form.form_errors.append("不能删除自己")
            form.disabled()
        elif target.is_superuser and not current_user.is_superuser:
            form.form_errors.append("无权删除超级管理员")
            form.disabled()
        elif form.validate():
            await service.delete(item_id)
            return self.htmx_success("删除成功")
        return self.htmx_render(
            template_name="user_destroy.html.j2",
            context={"form": form},
        )
