from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.enums import ScopeType
from litestar.middleware import ASGIMiddleware
from litestar.middleware.session.server_side import ServerSideSessionConfig
from litestar.response.redirect import ASGIRedirectResponse
from litestar.status_codes import HTTP_301_MOVED_PERMANENTLY
from litestar.types import ASGIApp, Receive, Scope, Send
from litestar.utils.path import normalize_path

if TYPE_CHECKING:
    from .settings import Settings


def create_middleware_config(settings: Settings):
    return [ServerSideSessionConfig().middleware]


class PathNormalizationMiddleware(ASGIMiddleware):
    """
    全站路径规范化中间件
    """

    scopes = (ScopeType.HTTP,)

    async def handle(
        self, scope: Scope, receive: Receive, send: Send, next_app: ASGIApp
    ) -> None:
        original_path = scope["raw_path"].decode("utf-8")

        normalized_path = normalize_path(original_path)

        # 对比逻辑：如果不一致，说明 URL 不规范
        if original_path != normalized_path:
            # 保留查询参数 (?page=1)
            query_string = scope.get("query_string", b"").decode("utf-8")
            redirect_path = (
                f"{normalized_path}?{query_string}" if query_string else normalized_path
            )

            # 直接拦截并跳转
            response = ASGIRedirectResponse(
                path=redirect_path, status_code=HTTP_301_MOVED_PERMANENTLY
            )
            await response(scope, receive, send)
            return

        # 一致则放行
        await next_app(scope, receive, send)
