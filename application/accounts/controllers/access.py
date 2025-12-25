from __future__ import annotations

from litestar import Controller, get, post, patch
from litestar.connection.request import Request
from litestar.exceptions import NotAuthorizedException

from application.deps import create_service_provider
from application.security import login_action, logout_action

from ..schemas import PasswordChangeSchema, UserLoginSchema, UserSchema
from ..services import UserService


class AccessController(Controller):
    tags = ["access (访问)"]

    dependencies = {
        "service": create_service_provider(UserService),
    }

    @get("/me")
    async def profile(self, request: Request, service: UserService) -> UserSchema:
        return service.to_schema(data=request.user, schema_type=UserSchema)

    @patch("/me/password")
    async def update_password(
        self, request: Request, data: PasswordChangeSchema, service: UserService
    ) -> UserSchema:
        # 验证旧密码
        if not request.user.password_hash.verify(data.old_password):
            raise NotAuthorizedException("当前密码错误")

        # 更新密码
        await service.update({"password_hash": data.new_password}, request.user.id)
        user = await service.get(request.user.id)
        return service.to_schema(data=user, schema_type=UserSchema)

    @post(path="/login", exclude_from_auth=True)
    async def login(
        self, request: Request, data: UserLoginSchema, service: UserService
    ) -> UserSchema:
        user = await service.get_one_or_none(username=data.username)

        if not user or not user.password_hash.verify(data.password):
            raise NotAuthorizedException("用户名或密码错误")

        # 检查用户状态
        if not user.is_active:
            raise NotAuthorizedException("用户已禁用")

        # 登陆操作
        login_action(request, user)
        # 返回用户信息
        return service.to_schema(data=user, schema_type=UserSchema)

    @post(path="/logout")
    async def logout(self, request: Request) -> None:
        logout_action(request)
