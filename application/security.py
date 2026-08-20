from __future__ import annotations

from functools import cached_property
from hashlib import sha256
from typing import Any, cast

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from litestar import Request
from litestar.config.app import AppConfig
from litestar.di import Provide
from litestar.exceptions import NotAuthorizedException
from litestar.middleware.session.client_side import (
    ClientSideSessionBackend,
    CookieBackendConfig,
)
from litestar.plugins import InitPlugin
from litestar.response import Redirect
from litestar.security.session_auth import SessionAuth
from litestar.types.empty import Empty
from sqlalchemy.orm import selectinload

from application.accounts.models import Role, User
from application.accounts.services import UserService
from application.config import cfg
from application.deps import provide_services
from application.htmx import ClientRedirect

USER_SESSION_KEY = "user"


def login_action(request: Request, user: User) -> None:
    request.session[USER_SESSION_KEY] = str(user.id)
    # 密码指纹: 改密后 hash_string 变, 指纹对不上 -> 旧 session 失效(踢出攻击者)
    # 用 hash_string 而非 str()(后者是 object repr, 含内存地址, 每次不同)
    request.session["pw_fp"] = user.password_hash.hash_string[-16:]


def logout_action(request: Request) -> None:
    # Empty: 响应时删除服务端存储 + 下发过期 cookie, 不留孤儿 session 文件
    request.scope["session"] = Empty


async def retrieve_user_handler(
    session: dict[str, Any], connection: Any
) -> User | None:
    user_id = session.get(USER_SESSION_KEY)
    async with provide_services(
        create_service_provider(UserService), connection=connection
    ) as (service,):
        user = await service.get_one_or_none(
            id=user_id, load=[selectinload(User.roles).selectinload(Role.permissions)]
        )
        if not user or not user.is_active:
            return None
        # 密码改过则旧 session 失效(指纹对不上)
        if session.get("pw_fp") != user.password_hash.hash_string[-16:]:
            return None
        return user


def not_authorized_handler(
    request: Request, exc: NotAuthorizedException
) -> Redirect | ClientRedirect:
    # 由路由名解析登录地址, 不写死路径(路由改名/加前缀时自动跟随)
    login_url = request.url_for("auth:login_view")
    if request.headers.get("HX-Request"):
        return ClientRedirect(redirect_to=login_url)
    return Redirect(path=login_url)


def provide_user(request: Request[User, Any, Any]) -> User:
    return cast(User, request.user)


class SecurityPlugin(InitPlugin):
    # 客户端 session (加密签名 cookie, 存浏览器): 服务器不落盘 ->
    # 无 session 文件堆积/IO/多 worker 共享存储问题, 且 pw_fp 指纹
    # 仍由 retrieve_user_handler 校验(改密踢出), 安全特性不丢。
    _SESSION_MAX_AGE = 86400 * 7

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        app_config = self.session_backend.on_app_init(app_config)
        app_config.dependencies["current_user"] = Provide(
            provide_user, sync_to_thread=False
        )
        app_config.exception_handlers[NotAuthorizedException] = not_authorized_handler
        return app_config

    @cached_property
    def session_backend(self) -> SessionAuth[User, ClientSideSessionBackend]:
        return SessionAuth[User, ClientSideSessionBackend](
            retrieve_user_handler=retrieve_user_handler,
            session_backend_config=CookieBackendConfig(
                # secret 必须 16/24/32 字节: sha256(secret_key) 得 32 字节 (256 bit)
                secret=sha256(cfg.secret_key.encode()).digest(),
                key="session",
                max_age=self._SESSION_MAX_AGE,
                # 生产环境 HTTPS 下标记 Secure, 防中间人截获 cookie; 开发 http 保持关闭
                secure=not cfg.debug,
                # 限制 cookie 仅同站携带, 防御跨站提交
                samesite="strict",
                httponly=True,
            ),
        )
