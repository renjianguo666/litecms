from __future__ import annotations

import itertools
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, cast

from jinja2 import Environment, FileSystemLoader
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.enums import MediaType
from litestar.exceptions import TemplateNotFoundException
from litestar.response.base import ASGIResponse, Response
from litestar.status_codes import HTTP_200_OK
from litestar.utils.deprecation import warn_deprecation

from application.config import cfg
from application.settings.manager import TemplateSettings
from application.web import helpers

if TYPE_CHECKING:
    from litestar.app import Litestar
    from litestar.background_tasks import BackgroundTask, BackgroundTasks
    from litestar.connection import Request
    from litestar.datastructures import Cookie
    from litestar.types import (
        Receive,
        ResponseCookies,
        Scope,
        Send,
        TypeEncodersMap,
    )


template_engine = JinjaTemplateEngine.from_environment(
    Environment(
        loader=FileSystemLoader(
            searchpath=[
                cfg.app_dir / "web/templates",
                cfg.root_dir / "storages/templates",
            ]
        ),
        enable_async=True,
    )
)
template_engine.engine.globals["settings"] = TemplateSettings()
template_engine.engine.globals["category_select"] = helpers.category_select
template_engine.engine.globals["tag_select"] = helpers.tag_select
template_engine.engine.globals["special_select"] = helpers.special_select
template_engine.engine.globals["article_select"] = helpers.article_select
template_engine.engine.globals["wechat_share"] = helpers.wechat_share


class Template(Response[bytes]):
    __slots__ = ("context", "template_names")

    def __init__(
        self,
        template_name: str | list[str],
        *,
        context: dict[str, Any] | None = None,
        background: BackgroundTask | BackgroundTasks | None = None,
        cookies: ResponseCookies | None = None,
        encoding: str = "utf-8",
        headers: dict[str, Any] | None = None,
        media_type: MediaType | str = MediaType.HTML,
        status_code: int = HTTP_200_OK,
    ) -> None:
        if isinstance(template_name, str):
            self.template_names = [template_name]
        else:
            self.template_names = template_name

        self.context = context or {}

        super().__init__(
            background=background,
            content=b"",
            cookies=cookies,
            encoding=encoding,
            headers=headers,
            media_type=media_type,
            status_code=status_code,
        )

    def create_template_context(self, request: Request) -> dict[str, Any]:
        return {**self.context, "request": request}

    def to_asgi_response(
        self,
        app: Litestar | None,
        request: Request,
        *,
        background: BackgroundTask | BackgroundTasks | None = None,
        cookies: Iterable[Cookie] | None = None,
        encoded_headers: Iterable[tuple[bytes, bytes]] | None = None,
        headers: dict[str, str] | None = None,
        is_head_response: bool = False,
        media_type: MediaType | str | None = None,
        status_code: int | None = None,
        type_encoders: TypeEncodersMap | None = None,
    ) -> ASGIResponse:
        if app is not None:
            warn_deprecation(
                version="2.1",
                deprecated_name="app",
                kind="parameter",
                removal_in="3.0.0",
                alternative="request.app",
            )

        headers = {**headers, **self.headers} if headers is not None else self.headers
        cookies = self.cookies if cookies is None else itertools.chain(self.cookies, cookies)

        template = None
        for template_name in self.template_names:
            try:
                template = template_engine.get_template(template_name)
                break
            except TemplateNotFoundException:
                continue

        if template is None:
            raise TemplateNotFoundException(template_name=self.template_names[0] if self.template_names else "")

        context = self.create_template_context(request)
        encoding = self.encoding
        response_background = self.background or background
        response_media_type = media_type or self.media_type
        response_status = self.status_code or status_code

        async def asgi_app(scope: Scope, receive: Receive, send: Send) -> None:
            # 渲染推迟到 ASGIApp 执行时: 此时在事件循环内, 可 await render_async,
            # async 模板标签 (category_select/article_select ...) 在渲染中
            # await 请求级共享 AsyncSession 查库。
            body = (await template.render_async(**context)).encode(encoding)
            response = ASGIResponse(
                background=response_background,
                body=body,
                content_length=None,
                cookies=cookies,
                encoded_headers=encoded_headers,
                encoding=encoding,
                headers=headers,
                is_head_response=is_head_response,
                media_type=response_media_type,
                status_code=response_status,
            )
            await response(scope, receive, send)

        # 渲染推迟到 asgi_app 执行, 类型上兼容基类返回 ASGIResponse (运行时为 ASGIApp)
        return cast(ASGIResponse, asgi_app)
