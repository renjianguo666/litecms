from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from functools import cached_property
from typing import Any, cast

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from litestar import Request
from litestar.config.app import AppConfig
from litestar.di import Provide
from litestar.exceptions import NotAuthorizedException
from litestar.middleware.session.server_side import (
    ServerSideSessionBackend,
    ServerSideSessionConfig,
)
from litestar.plugins import InitPlugin
from litestar.response import Redirect
from litestar.security.session_auth import SessionAuth
from litestar.stores.file import FileStore
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
    # session store 不单独建 FileStore: app 的 stores 即 cfg.stores
    # (default_factory 按名惰性创建, 目录 storages/runtime/sessions/),
    # 与响应缓存/taxonomies 缓存共用同一套 store 机制, 参数不漂移。
    _SESSION_MAX_AGE = 86400 * 7
    _SESSION_STORE_KEY = "sessions"

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        app_config = self.session_backend.on_app_init(app_config)
        app_config.dependencies["current_user"] = Provide(
            provide_user, sync_to_thread=False
        )
        app_config.exception_handlers[NotAuthorizedException] = not_authorized_handler
        self._setup_after_response(app_config)
        return app_config

    @cached_property
    def session_backend(self) -> SessionAuth[User, ServerSideSessionBackend]:
        return SessionAuth[User, ServerSideSessionBackend](
            retrieve_user_handler=retrieve_user_handler,
            session_backend_config=ServerSideSessionConfig(
                store=self._SESSION_STORE_KEY,
                max_age=self._SESSION_MAX_AGE,
                # 生产环境 HTTPS 下标记 Secure, 防中间人截获 cookie; 开发 http 保持关闭
                secure=not cfg.debug,
                # 限制 cookie 仅同站携带, 防御跨站提交
                samesite="strict",
            ),
        )

    def _setup_after_response(self, app_config: AppConfig) -> None:
        if app_config.after_response is None:
            app_config.after_response = self._cleanup_expired_sessions
        else:
            original = app_config.after_response

            async def combined(request: Request) -> None:
                result = original(request)
                if asyncio.iscoroutine(result):
                    await result
                await self._cleanup_expired_sessions(request)

            app_config.after_response = combined

    async def _cleanup_expired_sessions(self, request: Request) -> None:
        now = datetime.now(UTC)
        # 不传 default: key 不存在时返回 None, 用 None 区分"从未清理过"。
        # 若 default 填 now, 则 now-now==0 条件恒 False, key 永不写入 ->
        # 永远走 default -> 死循环, delete_expired() 一次都不执行。
        last_cleared = request.app.state.get("sessions_last_cleared")
        if last_cleared is None or now - last_cleared > timedelta(
            days=1
        ):  # 首次或每天清理一次
            # registry.get 类型上是 Store(基类), delete_expired 是 FileStore 专有;
            # 实际实现即 cfg.stores 的 default_factory 创建的 FileStore
            await cast(
                FileStore, request.app.stores.get(self._SESSION_STORE_KEY)
            ).delete_expired()
            request.app.state["sessions_last_cleared"] = now
