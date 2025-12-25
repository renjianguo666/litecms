from __future__ import annotations

from typing import Any, MutableMapping, Type, Union, cast

from advanced_alchemy.exceptions import IntegrityError, NotFoundError
from litestar import Request, Response
from litestar.exceptions import ValidationException
from litestar.status_codes import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)
from litestar.types import ExceptionHandler

# 错误消息中文映射（匹配英文消息关键词）
ERROR_MESSAGES = {
    "valid URL": "请输入有效的网址（如 https://example.com）",
    "required": "此字段必填",
    "string": "必须是字符串",
    "integer": "必须是整数",
    "number": "必须是数字",
    "boolean": "必须是布尔值",
    "email": "邮箱格式无效",
    "too short": "长度不足",
    "too long": "长度过长",
}


def validation_exception_handler(
    request: Request, exc: ValidationException
) -> Response:
    def translate(msg: str) -> str:
        for keyword, zh in ERROR_MESSAGES.items():
            if keyword in msg:
                return zh
        return msg

    extra_list = cast(list[dict[str, Any]], exc.extra or [])
    extra = [
        {"field": e.get("key", ""), "message": translate(e.get("message", ""))}
        for e in extra_list
    ]

    return Response(
        content={
            "status_code": HTTP_400_BAD_REQUEST,
            "detail": "验证失败",
            "extra": extra,
        },
        status_code=HTTP_400_BAD_REQUEST,
    )


def advanced_alchemy_not_found_handler(
    request: Request, exc: NotFoundError
) -> Response:
    return Response(
        content={
            "status_code": HTTP_404_NOT_FOUND,
            "detail": "请求的资源不存在",
        },
        status_code=HTTP_404_NOT_FOUND,
        media_type="application/json",
    )


def advanced_alchemy_integrity_error_handler(
    request: Request, exc: IntegrityError
) -> Response:
    return Response(
        content={
            "status_code": HTTP_409_CONFLICT,
            "detail": exc.detail,
        },
        status_code=HTTP_409_CONFLICT,
        media_type="application/json",
    )


ExceptionConfig = MutableMapping[Union[int, Type[Exception]], ExceptionHandler]


def create_exception_handlers() -> ExceptionConfig:
    return {
        ValidationException: validation_exception_handler,
        NotFoundError: advanced_alchemy_not_found_handler,
        IntegrityError: advanced_alchemy_integrity_error_handler,
    }
