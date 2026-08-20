from __future__ import annotations

from collections.abc import MutableMapping

from advanced_alchemy.exceptions import DuplicateKeyError, NotFoundError
from litestar import Request
from litestar.exceptions import (
    InternalServerException,
    MethodNotAllowedException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
)
from litestar.response import Template
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

__all__ = ["exception_handler"]


def bad_request_handler(request: Request, exc: Exception) -> Template:
    return Template(
        template_name="errors/400.html.j2", status_code=HTTP_400_BAD_REQUEST
    )


def permission_denied_handler(
    request: Request, exc: PermissionDeniedException
) -> Template:
    return Template(
        template_name="errors/403.html.j2",
        context={"msg": exc.detail},
        status_code=HTTP_403_FORBIDDEN,
    )


def not_found_handler(
    request: Request, exc: NotFoundError | NotFoundException
) -> Template:
    return Template(
        template_name="errors/404.html.j2",
        status_code=HTTP_404_NOT_FOUND,
    )


def internal_error_handler(request: Request, exc: Exception) -> Template:
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
