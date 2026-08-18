"""
HTMX 响应层：本站所有 HTMX 交互响应的统一出口。

核心设计 —— 双模式响应：
  同一个响应对象，根据请求是否携带 HX-Request 请求头，产生两种行为：

  - HX 请求（htmx 发起的页面内局部交互）：返回 200 + HX-* 响应头，
    htmx 前端按语义执行局部刷新 / 客户端跳转 / 弹 toast，页面不整跳；
  - 非 HX 请求（浏览器直接打开或提交，如直链访问、JS 禁用、外部表单）：
    退化为传统 HTTP 302 重定向（或整页渲染），保证功能不依赖前端可用。

安全基线 —— 防开放重定向：
  所有落到 Location / HX-Location 的重定向目标一律经 _safe_relative_url()
  剥离 scheme 与 netloc，只保留纯相对路径，杜绝被注入外部域名后
  浏览器 / htmx 将用户带到恶意站点。

模块导图：
  - _safe_relative_url     URL 净化工具（防开放重定向）
  - HTMXMixin              注入 controller 的便捷响应方法（toast / 跳转 / 渲染）
  - ClientRedirect         HX-Redirect：整页跳转（浏览器全刷新）
  - HXLocation             HX-Location：客户端路由跳转（无整页刷新）
  - HXTriggerLocation      HX-Location + HX-Trigger 组合：跳转 + 弹 toast 消息
  - HTMXBlockTemplate      块渲染：HX 只渲染 #workspace 内容块，非 HX 渲染整页
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict, Optional
from urllib.parse import quote, urlparse

from jinja2_fragments.litestar import HTMXBlockTemplate as _HTMXBlockTemplate
from litestar import Request
from litestar.plugins.htmx import HTMXTemplate
from litestar.response import Response
from litestar.response.base import ASGIResponse
from litestar.status_codes import HTTP_302_FOUND
from litestar.utils.deprecation import warn_deprecation
from litestar_htmx._utils import get_headers
from litestar_htmx.request import HTMXRequest
from litestar_htmx.response import ClientRedirect as _ClientRedirect
from litestar_htmx.response import HXLocation as _HXLocation
from litestar_htmx.types import (
    EventAfterType,
    HtmxHeaderType,
    LocationType,
    PushUrlType,
    ReSwapMethod,
    TriggerEventType,
)

if TYPE_CHECKING:
    from litestar.app import Litestar

__all__ = ["HTMXMixin", "HTMXRequest", "HTMXBlockTemplate", "HXLocation"]


DEFAULT_HX_TARGET = "#workspace"


def _safe_relative_url(url: str) -> str:
    """剥离 scheme/netloc 成纯相对路径, 防开放重定向。

    开放重定向漏洞: 若把用户可控字符串直接放进 Location 头,
    攻击者构造 `https://evil.com/x` 或 `//evil.com/x`(协议相对 URL,
    浏览器同样按外部域名解析), 可把用户跳去钓鱼站点。
    这里通过 urlparse 拆掉 scheme 和 netloc, 只留 path 及之后的部分:

    `https://evil.com/x` -> `/x`, `//evil.com/x` -> `/x`, `/path` 原样返回。

    反斜杠先归一化为正斜杠: 浏览器把 `\\evil.com` 当 `//evil.com`(协议相对)跳外站,
    而 urlparse 把它当 path、剥不掉 netloc, 会绕过。归一化后再剥, 并要求结果以 / 开头。
    """
    url = url.replace("\\", "/")
    result = urlparse(url)._replace(scheme="", netloc="").geturl()
    return result if result.startswith("/") else "/"


class HTMXMixin:
    """注入 controller 的 HTMX 响应方法集合。

    用法: controller 继承本 mixin 后, 可直接调用
      htmx_success("保存成功")        -> 200 + showToast 事件 + HX-Location 回跳
      htmx_error("操作失败")          -> 同上, toast 为 error 样式
      htmx_redirect("/target")        -> HX-Redirect 整页跳转
      htmx_location("/target")        -> HX-Location 客户端路由跳转
      htmx_render("tpl.html.j2", ctx) -> 渲染模板(局部块或整页, 见 HTMXBlockTemplate)
    """

    def htmx_redirect(self, redirect_to) -> ClientRedirect:
        """整页跳转: 对应 htmx 的 HX-Redirect 响应头, 浏览器全量刷新。"""
        return ClientRedirect(redirect_to=redirect_to)

    def _response_success_or_error(
        self,
        category,
        message,
        redirect: str | None = None,
        skip_redirect: bool = False,
    ) -> HXTriggerLocation:
        """构造 跳转 + toast 的组合响应, success/error 共用同一路径。

        - message:  toast 展示的文本(中文)
        - redirect: 成功/失败后跳转的路径, 缺省时由 HXTriggerLocation
                    从 HX-Current-URL/referer 自动推导(返回来源页)
        - skip_redirect: True 时不发 HX-Location, 只弹 toast(原地不跳)
        """
        return HXTriggerLocation(
            skip_redirect=skip_redirect,
            redirect_to=redirect,
            target=DEFAULT_HX_TARGET,
            trigger_name="showToast",
            trigger_params={"message": message, "type": category},
        )

    def htmx_success(
        self, message: str, redirect: str | None = None, skip_redirect: bool = False
    ) -> HXTriggerLocation:
        """操作成功 toast(绿色), 默认跳回来源页。"""
        return self._response_success_or_error(
            "success", message, redirect, skip_redirect
        )

    def htmx_error(
        self, message: str, redirect: str | None = None, skip_redirect: bool = False
    ) -> HXTriggerLocation:
        """操作失败 toast(红色), 默认停留在当前页。"""
        return self._response_success_or_error(
            "error", message, redirect, skip_redirect
        )

    def htmx_location(
        self,
        redirect_to: str,
        target: Optional[str] = DEFAULT_HX_TARGET,
        source: str | None = None,
        event: str | None = None,
        select: str | None = None,
        swap: ReSwapMethod | None = None,
        hx_headers: dict[str, Any] | None = None,
        values: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> HXLocation:
        """客户端路由跳转: HX-Location 头, 不整页刷新。

        参数即 htmx 文档中 HX-Location 的可选字段:
          target: 目标元素选择器(默认 #workspace)
          select: 从目标页中选取要插入的片段
          swap:   插入方式(outerHTML/innerHTML 等)
          values: 跳转附带提交的额外表单数据
        """
        return HXLocation(
            redirect_to=redirect_to,
            target=target,
            source=source,
            event=event,
            select=select,
            swap=swap,
            hx_headers=hx_headers,
            values=values,
            **kwargs,
        )

    def htmx_render(
        self,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
        block_name: Optional[str] = DEFAULT_HX_TARGET.replace("#", ""),
        block_names: Optional[list[str]] = None,
        push_url: Optional[PushUrlType] = None,
        re_swap: Optional[ReSwapMethod] = None,
        re_target: Optional[str] = None,
        trigger_event: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        after: Optional[EventAfterType] = None,
        **kwargs: Any,
    ) -> HTMXTemplate:
        """渲染模板: HX 请求只渲染目标块, 非 HX 请求渲染整页。

        默认 block_name="workspace": HX 请求仅渲染模板中
        {% block workspace %} 的内容插入页面, 其余部分不动;
        非 HX 请求由 HTMXBlockTemplate 自动降级为整页渲染(见该类注释)。
        """
        # 与 HXTriggerLocation 对齐:trigger_event 设置时,after 默认 "receive"
        # (htmx 事件在收到响应时立即触发, 而不是 settle/swap 之后)
        if trigger_event and after is None:
            after = "receive"

        if not block_name and not block_names:
            result = HTMXTemplate(
                push_url=push_url,
                re_swap=re_swap,
                re_target=re_target,
                trigger_event=trigger_event,
                params=params,
                after=after,
                template_name=template_name,
                context=context or {},
                **kwargs,
            )
        else:
            result = HTMXBlockTemplate(
                template_name=template_name,
                context=context or {},
                block_name=block_name,
                block_names=block_names,
                push_url=push_url,
                re_swap=re_swap,
                re_target=re_target,
                trigger_event=trigger_event,
                params=params,
                after=after,
                **kwargs,
            )

        # litestar_htmx 用 encode_json 生成 HX-Trigger header,默认不 ensure_ascii,
        # 中文 message 会导致 latin-1 编码失败。与 HXTriggerLocation.to_asgi_response
        # 中的处理保持一致:重新序列化为纯 ASCII
        if trigger_event:
            for header_name in (
                "HX-Trigger",
                "HX-Trigger-After-Settle",
                "HX-Trigger-After-Swap",
            ):
                if header_name in result.headers:
                    value = result.headers[header_name]
                    safe_value = json.dumps(json.loads(value), ensure_ascii=True)
                    result.headers[header_name] = safe_value

        return result


class ClientRedirect(_ClientRedirect):
    """整页跳转: HX-Redirect 响应头, 浏览器地址栏变化并全量刷新。

    双模式行为:
      - HX 请求:  返回 200 + HX-Redirect 头, htmx 前端执行整页跳转;
      - 非 HX 请求: 改写为 302 + Location, 浏览器传统重定向(两者最终都落到浏览器整页刷新)。

    基类 __init__ 里 del self.headers["Location"] 是构造流程内部清理:
    get_headers() 生成 HX-Redirect 时会附带一个空的 Location 头,
    基类将其删除(HTMX 语义不需要普通 Location), 无需子类处理。
    """

    def __init__(self, redirect_to: str, **kwargs) -> None:
        # 保存原始目标: 延迟到 to_asgi_response 阶段决定最终形态
        # (HX 分支直接透传; 非 HX 分支要经 _safe_relative_url 净化后再放 Location)
        self._redirect_to = redirect_to
        super().__init__(redirect_to=redirect_to, **kwargs)

    def to_asgi_response(
        self, app: Litestar | None, request: Request, **kwargs
    ) -> ASGIResponse:
        if app is not None:
            warn_deprecation(
                version="2.1",
                deprecated_name="app",
                kind="parameter",
                removal_in="3.0.0",
                alternative="request.app",
            )

        if not request.headers.get("HX-Request"):
            # 非 HX 请求(浏览器直开): 退化为标准 302 重定向。
            # Location 必须经 _safe_relative_url 净化, 防开放重定向。
            self.status_code = HTTP_302_FOUND
            self.headers.update({"Location": _safe_relative_url(self._redirect_to)})

        return super().to_asgi_response(app, request, **kwargs)


class HXLocation(_HXLocation):
    """客户端路由跳转: HX-Location 响应头, 页面不整刷、不离开。

    与 ClientRedirect 的区别:
      - HX-Redirect: 浏览器整页加载新地址(全刷新);
      - HX-Location: htmx 在后台请求目标页并替换指定区域(局部更新)。

    双模式行为:
      - HX 请求:  返回 200 + HX-Location 头, htmx 客户端路由跳转;
      - 非 HX 请求: 改写为 302 + Location, 浏览器传统重定向。

    基类 __init__ 中的 del self.headers["Location"] 同样在 super().__init__()
    内部完成: 基类把 URL 暂存在普通 Location 头中读回 path、拼出完整的
    HX-Location 头集合后删除临时载体, 无需子类处理。
    """

    def __init__(self, redirect_to: str, **kwargs) -> None:
        # 保存原始目标: 非 HX 分支需要它生成 302 的 Location(净化后)
        self._redirect_to = redirect_to
        super().__init__(redirect_to=redirect_to, **kwargs)

    def to_asgi_response(
        self, app: Litestar | None, request: Request, **kwargs
    ) -> ASGIResponse:
        if app is not None:
            warn_deprecation(
                version="2.1",
                deprecated_name="app",
                kind="parameter",
                removal_in="3.0.0",
                alternative="request.app",
            )

        if not request.headers.get("HX-Request"):
            # 非 HX 请求(浏览器直开): 退化为标准 302 重定向, 目标同样净化
            self.status_code = HTTP_302_FOUND
            self.headers.update({"Location": _safe_relative_url(self._redirect_to)})

        return super().to_asgi_response(app, request, **kwargs)


class HXTriggerLocation(Response):
    """组合响应: HX-Location(跳转) + HX-Trigger(弹 toast), 全站表单提交的默认出口。

    典型链路(表单提交成功):
      controller 返回 htmx_success("保存成功")
      -> 响应头携带 HX-Location(目标路径) 与 HX-Trigger(showToast 事件)
      -> htmx 客户端按 HX-Location 请求目标页替换 #workspace 区域,
         同时触发 showToast 事件, 页面右上角弹出 success toast

    响应头行为:
      - HX 请求:
        1) 未 skip_redirect 时生成 HX-Location, 目标按优先级取
           显式 redirect_to > query 参数 url > HX-Current-URL > referer > "/"
           (表单页通过 hx-vals 携带当前 url, 提交后即可回到来源页);
        2) 有 trigger_name 时生成 HX-Trigger(showToast), 中文消息需
           ensure_ascii 重序列化(否则 latin-1 编码报错);
      - 非 HX 请求(浏览器直接提交表单): 退化为 302 重定向,
        目标取 redirect_to 或 "/", 同样经 _safe_relative_url 净化。

    为什么参数延迟到 to_asgi_response 才用:
      Response 对象在 controller 中构造(此时请求尚未进入), 而是否
      走 HX 分支依赖请求头, 故 __init__ 只保存参数, 在响应阶段决定形态。
    """

    def __init__(
        self,
        skip_redirect: bool = False,
        # HX-Location 参数
        redirect_to: str | None = None,
        source: str | None = None,
        event: str | None = None,
        target: str | None = None,
        select: str | None = None,
        swap: ReSwapMethod | None = None,
        hx_headers: dict[str, Any] | None = None,
        values: dict[str, str] | None = None,
        # HX-Trigger 参数
        trigger_name: str | None = None,
        trigger_params: dict[str, Any] | None = None,
        trigger_after: EventAfterType = "receive",
        **kwargs,
    ):
        kwargs.setdefault("media_type", "text/html; charset=utf-8")
        super().__init__(content=None, status_code=200, **kwargs)
        # 保存参数（延迟到 to_asgi_response 使用, 见类注释）
        self._skip_redirect = skip_redirect
        self._redirect_to = redirect_to
        self._source = source
        self._event = event
        self._target = target
        self._select = select
        self._swap: ReSwapMethod = swap
        self._hx_headers = hx_headers
        self._values = values
        self._trigger_name = trigger_name
        self._trigger_params = trigger_params
        self._trigger_after: EventAfterType = trigger_after

    def to_asgi_response(
        self, app: Litestar | None, request: Request, **kwargs
    ) -> ASGIResponse:
        if app is not None:
            warn_deprecation(
                version="2.1",
                deprecated_name="app",
                kind="parameter",
                removal_in="3.0.0",
                alternative="request.app",
            )

        if not request.headers.get("HX-Request"):
            # 非 HX 请求(浏览器直接提交): 退化为 302 重定向,
            # 无显式目标时保底 "/"; 与 HX 分支一致, 剥离 scheme/netloc 防开放重定向
            self.status_code = HTTP_302_FOUND
            self.headers.update(
                {"Location": _safe_relative_url(self._redirect_to or "/")}
            )
            return super().to_asgi_response(app, request, **kwargs)

        if not self._skip_redirect:
            # 1. 优先级：明确指定的路径 > HX-Current-URL > referer > 默认保底 "/"
            #    (表单页模板用 hx-vals 把当前 url 放进 query, 提交成功后跳回来源页)
            raw_url = (
                self._redirect_to
                or request.query_params.get("url")
                or request.headers.get("HX-Current-URL")
                or request.headers.get("referer", "/")
            )

            # 2. 暴力砍掉协议和域名，生成纯相对路径（防开放重定向）
            relative_url = _safe_relative_url(raw_url)

            # 3. 组装 HX-Location 头: path 经 quote 只保留安全字符,
            #    避免特殊字符破坏响应头结构
            self.headers.update(
                get_headers(
                    HtmxHeaderType(
                        location=LocationType(
                            path=quote(relative_url, safe="/#%[]=:;$&()+,!?*@'~"),
                            source=self._source,
                            event=self._event,
                            target=self._target,
                            select=self._select,
                            swap=self._swap,
                            values=self._values,
                            hx_headers=self._hx_headers,
                        )
                    )
                )
            )

        if self._trigger_name:
            # 生成 HX-Trigger(showToast 事件), 触发前端 toast
            raw_headers = get_headers(
                HtmxHeaderType(
                    trigger_event=TriggerEventType(
                        name=self._trigger_name,
                        params=self._trigger_params,
                        after=self._trigger_after,
                    )
                )
            )

            # litestar_htmx 序列化 HX-Trigger 默认不 ensure_ascii,
            # 中文 message 落进 latin-1 编码的响应头会失败, 这里重序列化为纯 ASCII
            for key, value in raw_headers.items():
                safe_value = json.dumps(json.loads(value), ensure_ascii=True)
                self.headers.update({key: safe_value})

        return super().to_asgi_response(app, request, **kwargs)


class HTMXBlockTemplate(_HTMXBlockTemplate):
    """块渲染降级: HX 只渲染目标块, 非 HX 自动渲染整页。

    HX 请求: 只渲染 template 中 block_name 指定的块(默认 #workspace 对应
    {% block workspace %}), 其余页面结构由浏览器端已有 DOM 提供;
    非 HX 请求(直链访问/JS 禁用): block_name 置 None, 整页渲染,
    保证用户直接打开 URL 看到完整页面。
    """

    def to_asgi_response(
        self, app: Litestar | None, request: Request, **kwargs: Any
    ) -> ASGIResponse:
        if app is not None:
            warn_deprecation(
                version="2.1",
                deprecated_name="app",
                kind="parameter",
                removal_in="3.0.0",
                alternative="request.app",
            )

        if not request.headers.get("HX-Request"):
            # 非 HX 请求: 取消块裁剪, 降级为整页渲染
            self.block_name = None
            self.block_names = None

        # 3. 干净地原封不动抛给父类去处理
        return super().to_asgi_response(app, request, **kwargs)
