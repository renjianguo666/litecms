from __future__ import annotations

import logging
from sys import stderr, stdout
from typing import TYPE_CHECKING, Literal

import structlog
from litestar.logging.config import (
    LoggingConfig,
    StructLoggingConfig,
    default_logger_factory,
    default_structlog_processors,
    default_structlog_standard_lib_processors,
)
from litestar.middleware.logging import LoggingMiddlewareConfig
from litestar.plugins.structlog import StructlogConfig

if TYPE_CHECKING:
    from .settings import Settings


def create_structlog_config(settings: Settings) -> StructlogConfig:
    def _is_tty() -> bool:
        return bool(stderr.isatty() or stdout.isatty())

    _render_as_json = not _is_tty()
    _structlog_default_processors = default_structlog_processors(
        as_json=_render_as_json
    )
    _structlog_default_processors.insert(
        1, structlog.processors.EventRenamer("message")
    )
    _structlog_standard_lib_processors = default_structlog_standard_lib_processors(
        as_json=_render_as_json
    )
    _structlog_standard_lib_processors.insert(
        1, structlog.processors.EventRenamer("message")
    )

    # 根据 debug 模式动态设置日志级别
    if settings.debug:
        # 开发环境：显示更详细的日志
        LOG_LEVEL = logging.DEBUG
        ASGI_ERROR_LEVEL = logging.DEBUG
        ASGI_ACCESS_LEVEL = logging.INFO
        SQLALCHEMY_LEVEL = logging.DEBUG
    else:
        # 生产环境：只显示重要日志
        LOG_LEVEL = logging.WARNING
        ASGI_ERROR_LEVEL = logging.WARNING
        ASGI_ACCESS_LEVEL = logging.WARNING
        SQLALCHEMY_LEVEL = logging.WARNING

    REQUEST_FIELDS: list[Literal["path", "method", "query", "path_params"]] = [
        "path",
        "method",
        "query",
        "path_params",
    ]
    RESPONSE_FIELDS: list[Literal["status_code"]] = ["status_code"]

    return StructlogConfig(
        structlog_logging_config=StructLoggingConfig(
            log_exceptions="always",
            processors=_structlog_default_processors,
            logger_factory=default_logger_factory(as_json=_render_as_json),
            standard_lib_logging_config=LoggingConfig(
                root={
                    "level": logging.getLevelName(LOG_LEVEL),
                    "handlers": ["queue_listener"],
                },
                formatters={
                    "standard": {
                        "()": structlog.stdlib.ProcessorFormatter,
                        "processors": _structlog_standard_lib_processors,
                    },
                },
                loggers={
                    "_granian": {
                        "propagate": False,
                        "level": logging.getLevelName(ASGI_ERROR_LEVEL),
                        "handlers": ["queue_listener"],
                    },
                    "granian.server": {
                        "propagate": False,
                        "level": logging.getLevelName(ASGI_ERROR_LEVEL),
                        "handlers": ["queue_listener"],
                    },
                    "granian.access": {
                        "propagate": False,
                        "level": logging.getLevelName(ASGI_ACCESS_LEVEL),
                        "handlers": ["queue_listener"],
                    },
                    "sqlalchemy.engine": {
                        "propagate": False,
                        "level": logging.getLevelName(SQLALCHEMY_LEVEL),
                        "handlers": ["queue_listener"],
                    },
                    "sqlalchemy.pool": {
                        "propagate": False,
                        "level": logging.getLevelName(SQLALCHEMY_LEVEL),
                        "handlers": ["queue_listener"],
                    },
                },
            ),
        ),
        middleware_logging_config=LoggingMiddlewareConfig(
            request_log_fields=REQUEST_FIELDS,
            response_log_fields=RESPONSE_FIELDS,
        ),
    )
