from litestar import Request
from litestar.enums import ScopeType
from litestar.middleware import ASGIMiddleware
from litestar.response.base import ASGIResponse
from litestar.types import ASGIApp, Receive, Scope, Send

from application.config import config

# from .services import SiteRepository


class SiteMiddleware(ASGIMiddleware):
    """站点匹配中间件"""

    scopes = (ScopeType.HTTP, ScopeType.ASGI)

    async def handle(
        self, scope: Scope, receive: Receive, send: Send, next_app: ASGIApp
    ) -> None:
        await next_app(scope, receive, send)

    # async def handle(
    #     self, scope: Scope, receive: Receive, send: Send, next_app: ASGIApp
    # ) -> None:
    #     request = Request(scope)
    #     hostname = request.url.hostname

    #     # 本地开发使用临时站点
    #     if hostname in ("127.0.0.1", "localhost"):
    #         # from .schemas import SiteSchema, SiteSettingsSchema

    #         scope["state"]["site"] = SiteSchema(
    #             name="Development",
    #             domain=hostname,
    #             is_active=True,
    #             priority=0,
    #             settings=SiteSettingsSchema(scheme="http"),
    #         )
    #         await next_app(scope, receive, send)
    #         return

    #     async with config.plugins.sqlalchemy.provide_session(
    #         request.app.state, scope
    #     ) as session:
    #         repo = SiteRepository(session=session)
    #         site = await repo.get_one_or_none(domain=hostname)

    #     if site is None:
    #         response = ASGIResponse(body="域名未授权", status_code=403)
    #         await response(scope, receive, send)
    #         return

    #     scope["state"]["site"] = site

    #     await next_app(scope, receive, send)
