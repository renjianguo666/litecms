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
from sqlalchemy.pool import AsyncAdaptedQueuePool

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
        # SQLite 用有界连接池而非 NullPool: NullPool 每请求新建连接,
        # 爬虫风暴下连接/线程无限堆积(aiosqlite 每连接一个线程) → 内存涨 OOM。
        # QueuePool 8 连接封顶 + 复用, WAL 下读写安全, 连接线程稳定。
        engine_kwargs.update(
            poolclass=AsyncAdaptedQueuePool,
            pool_size=8,
            max_overflow=0,
        )
        engine = create_async_engine(**engine_kwargs)

        @event.listens_for(engine.sync_engine, "connect")
        def _sqla_on_connect_sqlite(dbapi_connection: Any, _: Any) -> None:
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA foreign_keys=ON;")

                cursor.execute("PRAGMA synchronous=NORMAL;")
                # 页缓存/mmap 是每连接独立的: 有界连接池 8 连接 × 6.4MB 封顶,
                # 读缓存由 OS page cache 兜底。曾用 256MB/-64000(62.5MB) 在
                # NullPool 下随连接暴涨吃满 cgroup 内存 → OOM(272af63 回归)。
                cursor.execute("PRAGMA mmap_size = 0;")
                cursor.execute("PRAGMA cache_size = -6400;")
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
