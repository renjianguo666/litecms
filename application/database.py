from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from litestar.plugins.sqlalchemy import (
    AlembicAsyncConfig,
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
)
from litestar.serialization import decode_json, encode_json
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from .config import Config, cfg


def create_sqlalchemy_engine(config: Config) -> AsyncEngine:
    """
    创建同步数据库引擎。
    - PostgreSQL: 开启连接池健康检查，使用 Litestar 的高效 JSON 序列化。
    - SQLite: 开启 WAL 模式、外键约束，并优化锁处理机制。
    """
    engine_kwargs = {
        "url": config.database_url,
        "future": True,
        "json_serializer": encode_json,
        "json_deserializer": decode_json,
        # "echo": config.debug or config.database_echo,
    }

    scheme = urlparse(config.database_url).scheme or ""

    if scheme.startswith("postgres"):
        engine_kwargs["pool_pre_ping"] = True
        return create_async_engine(**engine_kwargs)

    elif scheme.startswith("sqlite"):
        engine_kwargs["poolclass"] = NullPool
        engine = create_async_engine(**engine_kwargs)

        @event.listens_for(engine.sync_engine, "connect")
        def _sqla_on_connect_sqlite(dbapi_connection: Any, _: Any) -> None:
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA foreign_keys=ON;")

                cursor.execute("PRAGMA synchronous=NORMAL;")
                cursor.execute("PRAGMA mmap_size = 268435456;")
                cursor.execute("PRAGMA cache_size = -64000;")
                cursor.execute("PRAGMA temp_store=MEMORY;")
                cursor.execute("PRAGMA busy_timeout=30000;")

                dbapi_connection.isolation_level = None
            finally:
                cursor.close()

        @event.listens_for(engine.sync_engine, "begin")
        def _sqla_on_begin_sqlite(dbapi_connection: Any) -> None:
            dbapi_connection.exec_driver_sql("BEGIN")

        return engine

    return create_async_engine(**engine_kwargs)


def create_sqlalchemy_config() -> SQLAlchemyAsyncConfig:
    return SQLAlchemyAsyncConfig(
        engine_instance=create_sqlalchemy_engine(cfg),
        before_send_handler="autocommit",
        session_config=AsyncSessionConfig(expire_on_commit=False),
        alembic_config=AlembicAsyncConfig(
            script_location=(cfg.root_dir / "migrations").as_posix(),
        ),
    )


sqlalchemy_config = create_sqlalchemy_config()
