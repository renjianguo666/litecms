from __future__ import annotations

import logging
from sys import stderr, stdout
from typing import Literal

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

from application.config import cfg


def create_structlog_config() -> StructlogConfig:
    """构造 structlog 结构化日志配置(仿老项目, 读 cfg.debug)。

    - 生产环境 root 仅 WARNING 及以上: 抑制爬虫/扫描器高频请求的
      异常日志刷屏(405 等走轻量 handler 不打 traceback, 见 exceptions.py)。
    - log_exceptions="debug": 生产不记录异常栈(内存安全), debug 记录。
    - 输出: 非 TTY(生产被 systemd 重定向到文件)走 JSON, TTY(开发)走友好文本。
    """

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
    if cfg.debug:
        LOG_LEVEL = logging.DEBUG
        ASGI_ERROR_LEVEL = logging.DEBUG
        ASGI_ACCESS_LEVEL = logging.INFO
        # INFO 保留 SQL 语句文本 (SELECT/INSERT...);
        # 不设 DEBUG: 否则每条 dbapi 操作都打 executing/operation completed
        # 连 PRAGMA foreign_keys 等建连内部语句都刷屏
        SQLALCHEMY_LEVEL = logging.INFO
    else:
        LOG_LEVEL = logging.WARNING
        ASGI_ERROR_LEVEL = logging.WARNING
        ASGI_ACCESS_LEVEL = logging.WARNING
        SQLALCHEMY_LEVEL = logging.WARNING

    # aiosqlite 驱动自身的 DEBUG 日志: 每条底层调用都刷 executing/completed 两行,
    # 且会冒泡到 DEBUG 的 root, 是 SQL 刷屏的主要来源; 与 sqlalchemy.engine 的
    # SQL 语句日志无关, 直接抬到 WARNING 关掉 (本驱动无 INFO 级日志可保留)
    AIOSQLITE_LEVEL = logging.WARNING

    REQUEST_FIELDS: list[
        Literal["path", "method", "query", "path_params"]
    ] = ["path", "method", "query", "path_params"]
    RESPONSE_FIELDS: list[Literal["status_code"]] = ["status_code"]

    return StructlogConfig(
        structlog_logging_config=StructLoggingConfig(
            # 生产不记录异常栈(内存安全); debug 记录完整 traceback
            log_exceptions="debug",
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
                    "aiosqlite": {
                        "propagate": False,
                        "level": logging.getLevelName(AIOSQLITE_LEVEL),
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


# 模块级实例, 仿 database.py 的 sqlalchemy_config 模式:
# 插件模块直接引用, 进程内只构造一次
structlog_config = create_structlog_config()
