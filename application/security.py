from __future__ import annotations

from functools import cached_property
from typing import Any, cast

from litestar.config.app import AppConfig
from litestar.connection import ASGIConnection, Request
from litestar.di import Provide
from litestar.exceptions import NotAuthorizedException
from litestar.middleware.authentication import AuthenticationResult
from litestar.middleware.session.server_side import (
    ServerSideSessionBackend,
    ServerSideSessionConfig,
)
from litestar.plugins.base import CLIPlugin, InitPluginProtocol
from litestar.security.session_auth import SessionAuth
from litestar.security.session_auth.middleware import SessionAuthMiddleware

from application.accounts.models import User
from application.accounts.services import UserService
from application.config import config

USER_SESSION_KEY = "user_id"


def login_action(request: Request, user: User) -> None:
    request.session[USER_SESSION_KEY] = user.id


def logout_action(request: Request) -> None:
    request.session.clear()


class SecurityPlugin(InitPluginProtocol, CLIPlugin):
    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        app_config.dependencies["current_user"] = Provide(self.provide_user)
        """应用初始化时注册认证"""
        self.session_backend.on_app_init(app_config)
        return app_config

    @staticmethod
    async def provide_user(request: Request[User, Any, Any]) -> User | None:
        return cast(User, request.user)

    async def retrieve_session_user_handler(
        self, session: dict[str, Any], connection: ASGIConnection
    ) -> User | None:
        user_id = session.get(USER_SESSION_KEY)

        db_session = config.plugins.sqlalchemy.provide_session(
            connection.app.state, connection.scope
        )
        service = UserService(session=db_session)
        user = await service.get_one_or_none(id=user_id)
        return user if user and user.is_active else None

    @cached_property
    def session_backend(self):
        return SessionAuth[
            User, ServerSideSessionBackend
        ](
            retrieve_user_handler=self.retrieve_session_user_handler,
            session_backend_config=ServerSideSessionConfig(),
            authentication_middleware_class=CustomSessionAuthMiddleware,  # 👈 使用自定义中间件
            # exclude=[r"^(?!.*\/api).*$"],
            exclude="^/(?!api/).+$",
        )


class CustomSessionAuthMiddleware(SessionAuthMiddleware):
    """自定义 Session 认证中间件，提供中文错误消息"""

    error_map = {
        "no session data found": "未登录或登录已过期，请重新登录",
        "no user correlating to session found": "用户信息无效或已被禁用",
    }

    async def authenticate_request(
        self, connection: ASGIConnection
    ) -> AuthenticationResult:
        """认证请求，自定义错误消息"""
        try:
            return await super().authenticate_request(connection)
        except NotAuthorizedException as e:
            message = str(e.detail)
            if message in self.error_map:
                raise NotAuthorizedException(self.error_map[message]) from e

            raise  # 未匹配到，保持原样
