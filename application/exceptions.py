from __future__ import annotations

import html
import traceback
from collections.abc import MutableMapping
from pathlib import Path

from advanced_alchemy.exceptions import DuplicateKeyError, NotFoundError
from jinja2.exceptions import TemplateError
from litestar import Request
from litestar.enums import MediaType
from litestar.exceptions import (
    InternalServerException,
    MethodNotAllowedException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from litestar.response import Response, Template
from litestar.status_codes import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_409_CONFLICT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from litestar.types import ExceptionHandler

from application.checks import PathConflictError
from application.config import cfg


def _get_template_dev_mode() -> bool:
    """读模板开发者模式开关。逻辑在 themes 模块, 懒加载避免循环依赖。"""
    from application.themes.utils import get_template_dev_mode

    return get_template_dev_mode()


__all__ = ["exception_handler"]


def bad_request_handler(request: Request, exc: Exception) -> Template:
    return Template(template_name="errors/400.html.j2", status_code=HTTP_400_BAD_REQUEST)


def permission_denied_handler(request: Request, exc: PermissionDeniedException) -> Template:
    return Template(
        template_name="errors/403.html.j2",
        context={"msg": exc.detail},
        status_code=HTTP_403_FORBIDDEN,
    )


def not_found_handler(request: Request, exc: NotFoundError | NotFoundException) -> Template:
    return Template(
        template_name="errors/404.html.j2",
        status_code=HTTP_404_NOT_FOUND,
    )


def internal_error_handler(request: Request, exc: Exception) -> Template | Response:
    # debug 打完整 traceback 便于排查; 生产只打一行摘要(可查问题, 不刷屏):
    # 爬虫/扫描器高频请求若每个异常都 logger.exception 打完整 traceback,
    # 日志队列会堆积 -> 内存持续上涨。摘要行含 method/path/异常类型, 够定位。
    if request.app.debug:
        request.logger.exception("Unhandled exception")
    else:
        request.logger.error(
            "500: %s %s -> %s",
            request.method,
            request.url.path,
            type(exc).__name__,
        )
    # 模板开发者模式: settings.toml 开关(mtime 热重载, 无需重启)。
    # 开启时前台模板错误输出带"文件:行号"的开发者详情页; 关闭时前台纯净 500。
    # 开关入口在「模板管理」页头, 不依赖 session/DB; 访客默认零泄露。
    if isinstance(exc, TemplateError) and _get_template_dev_mode():
        return template_error_response(exc)
    return Template(
        template_name="errors/500.html.j2",
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
    )


def method_not_allowed_handler(request: Request, exc: Exception) -> Template:
    # 单独处理, 不落入 Exception 兜底: 扫描器常用 HEAD 探测路径,
    # 405 若走 internal_error_handler 会打 traceback 刷日志。
    # 轻量返回 404 页面 (扫描器无权限判断该路径是否有效)。
    return Template(
        template_name="errors/404.html.j2",
        status_code=HTTP_405_METHOD_NOT_ALLOWED,
    )


def conflict_handler(request: Request, exc: Exception) -> Template:
    return Template(template_name="errors/409.html.j2", status_code=HTTP_409_CONFLICT)


ExceptionConfig = MutableMapping[int | type[Exception], ExceptionHandler]

exception_handler: ExceptionConfig = {
    PathConflictError: bad_request_handler,
    ValidationException: bad_request_handler,
    PermissionDeniedException: permission_denied_handler,
    NotFoundError: not_found_handler,
    NotFoundException: not_found_handler,
    MethodNotAllowedException: method_not_allowed_handler,
    HTTP_409_CONFLICT: conflict_handler,
    DuplicateKeyError: conflict_handler,
    InternalServerException: internal_error_handler,
    Exception: internal_error_handler,
}


# =========================================================
# 模板错误详情页 (管理员可见, 独立 HTML, 不依赖模板引擎)
# =========================================================


def _display_path(filename: str) -> str:
    """绝对路径转相对项目根, 避免向管理员页面泄露服务器路径。

    /home/user/.../application/web/templates/x.html -> application/web/templates/x.html
    不在项目根内的文件(如外部模板)保持原样, 不强行裁剪。
    """
    try:
        return str(Path(filename).resolve().relative_to(cfg.root_dir))
    except ValueError:
        return filename


def template_error_location(exc: Exception) -> str:
    """提取"模板文件:行号"用于管理员详情页。

    TemplateSyntaxError/TemplateRuntimeError 自带 filename/lineno(含 include
    引入的文件, filename 指向真正坏的那个); UndefinedError 等运行时错误无
    filename, 从 traceback 帧里找模板帧兜底(endswith 精确匹配模板后缀,
    不误判含 templates 的 Python 包路径)。非模板异常返回空串。
    返回相对项目根的路径, 不泄露服务器绝对路径。
    """
    filename = getattr(exc, "filename", None)
    if filename:
        lineno = getattr(exc, "lineno", None)
        loc = f"{filename}:{lineno}" if lineno else str(filename)
        return _display_path(loc)
    tb = exc.__traceback__
    if tb is not None:
        for frame in traceback.extract_tb(tb):
            if str(frame.filename).endswith((".html", ".html.j2")):
                return _display_path(f"{frame.filename}:{frame.lineno}")
    return ""


def _error_snippet(location: str) -> str:
    """从"文件:行号"读取该行源码, 作为代码片段展示; 读不到就空。

    location 是相对项目根的展示路径(见 template_error_location), 读文件时
    拼回项目根; 绝对路径(项目外文件)则直接用。
    """
    if not location:
        return ""
    path_part, _, line_part = location.rpartition(":")
    if not line_part.isdigit():
        return ""
    path = Path(path_part)
    if not path.is_absolute():
        path = cfg.root_dir / path
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return ""
    n = int(line_part)
    if not (1 <= n <= len(lines)):
        return ""
    code = html.escape(lines[n - 1].strip())
    return f'<div class="snippet"><span style="color:#78716c">{n}</span>  {code}</div>'


_TEMPLATE_ERROR_CSS = (
    '*{box-sizing:border-box}'
    'body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,'
    "'PingFang SC','Microsoft YaHei',sans-serif;"
    "background:#f5f5f4;color:#292524;margin:0;padding:2rem;min-height:100vh;"
    "display:flex;align-items:flex-start;justify-content:center}"
    ".card{width:100%;max-width:760px;background:#fff;border:1px solid #e7e5e4;"
    "border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,.08);overflow:hidden}"
    ".head{background:linear-gradient(135deg,#dc2626,#991b1b);color:#fff;"
    "padding:1.5rem 2rem}"
    ".head h1{margin:0;font-size:1.25rem;font-weight:600}"
    ".head .type{margin-top:.5rem;display:inline-block;"
    "font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.85rem;"
    "background:rgba(0,0,0,.25);padding:.3rem .6rem;border-radius:6px}"
    ".body{padding:1.5rem 2rem 2rem}"
    ".row{display:flex;gap:1rem;padding:.75rem 0;border-bottom:1px solid #f5f5f4;"
    "font-size:.9rem}"
    ".row:last-of-type{border-bottom:none}"
    ".label{flex-shrink:0;width:5rem;color:#a8a29e;font-size:.8rem;padding-top:.1rem}"
    ".value{word-break:break-all;font-family:ui-monospace,SFMono-Regular,Menlo,"
    "monospace;line-height:1.5}"
    ".value.err{color:#dc2626}"
    ".snippet{margin-top:1rem;background:#1c1917;color:#a7f3d0;padding:.8rem 1rem;"
    "border-radius:8px;border-left:4px solid #dc2626;"
    "font-family:ui-monospace,Menlo,monospace;font-size:.85rem;white-space:pre-wrap;"
    "overflow-x:auto}"
    ".hint{margin-top:1.25rem;font-size:.8rem;color:#a8a29e}"
)

def template_error_response(exc: Exception) -> Response:
    """管理员可见的模板错误详情页。

    独立 HTML Response + 内联 CSS: web 模块用的是独立 jinja2 引擎, 后台引擎
    与之不同——错误页若走模板引擎就是引擎错位 + 双重依赖(引擎再出错则错误页
    本身 500)。独立 HTML 不依赖任何引擎, 彻底免疫。仅登录管理员可见。
    """
    kind = html.escape(type(exc).__name__)
    location = html.escape(template_error_location(exc))
    error = html.escape(str(exc))
    snippet = _error_snippet(template_error_location(exc))
    content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>模板渲染错误</title>
<style>
  {_TEMPLATE_ERROR_CSS}
</style>
</head>
<body>
  <div class="card">
    <div class="head">
      <h1>模板渲染错误 (500)</h1>
      <span class="type">{kind}</span>
    </div>
    <div class="body">
      <div class="row"><div class="label">模板文件</div><div class="value err">{location}</div></div>
      <div class="row"><div class="label">错误信息</div><div class="value">{error}</div></div>
      {snippet}
      <p class="hint">到后台「模板管理」修正该模板后重试。此详情仅登录管理员可见，访客看到的是通用 500 页面。</p>
    </div>
  </div>
</body>
</html>"""
    return Response(content=content, media_type=MediaType.HTML, status_code=HTTP_500_INTERNAL_SERVER_ERROR)
