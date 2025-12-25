from __future__ import annotations

from typing import TYPE_CHECKING, Any

from litestar.plugins.sqlalchemy import (
    AlembicAsyncConfig,
    AsyncSessionConfig,
    SQLAlchemyAsyncConfig,
)
from litestar.serialization import decode_json, encode_json
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

if TYPE_CHECKING:
    from .settings import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    # 确定是否开启回显：如果在 debug 模式或者是显式开启了 database_echo
    should_echo = settings.debug or settings.database_echo

    engine_kwargs = {
        "url": settings.database_url,
        "future": True,
        "json_serializer": encode_json,
        "json_deserializer": decode_json,
        "echo": should_echo,
    }

    if settings.database_url.startswith("postgresql"):
        engine = create_async_engine(**engine_kwargs)

        @event.listens_for(engine.sync_engine, "connect")
        def _sqla_on_connect_pg(dbapi_connection: Any, _: Any) -> Any:
            def encoder(bin_value: bytes) -> bytes:
                return b"\x01" + encode_json(bin_value)

            def decoder(bin_value: bytes) -> Any:
                return decode_json(bin_value[1:])

            dbapi_connection.await_(
                dbapi_connection.driver_connection.set_type_codec(
                    "jsonb",
                    encoder=encoder,
                    decoder=decoder,
                    schema="pg_catalog",
                    format="binary",
                ),
            )
            dbapi_connection.await_(
                dbapi_connection.driver_connection.set_type_codec(
                    "json",
                    encoder=encoder,
                    decoder=decoder,
                    schema="pg_catalog",
                    format="binary",
                ),
            )

    elif settings.database_url.startswith("sqlite"):
        engine_kwargs["poolclass"] = NullPool
        engine = create_async_engine(**engine_kwargs)

        @event.listens_for(engine.sync_engine, "connect")
        def _sqla_on_connect_sqlite(dbapi_connection: Any, _: Any) -> Any:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()
            dbapi_connection.isolation_level = None

        @event.listens_for(engine.sync_engine, "begin")
        def _sqla_on_begin_sqlite(dbapi_connection: Any) -> Any:
            dbapi_connection.exec_driver_sql("BEGIN IMMEDIATE")

    else:
        engine = create_async_engine(**engine_kwargs)

    return engine


def create_sqlalchemy_config(settings: Settings) -> SQLAlchemyAsyncConfig:
    return SQLAlchemyAsyncConfig(
        engine_instance=create_engine(settings),
        before_send_handler="autocommit",
        session_config=AsyncSessionConfig(expire_on_commit=False),
        alembic_config=AlembicAsyncConfig(
            script_location=(settings.app_dir.parent / "migrations").as_posix(),
        ),
    )
