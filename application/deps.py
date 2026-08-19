from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

from litestar.connection import ASGIConnection
from sqlalchemy.ext.asyncio import AsyncSession

from application.database import sqlalchemy_config


@asynccontextmanager
async def provide_services(
    *providers: Callable[..., AsyncGenerator[Any]],
    session: AsyncSession | None = None,
    connection: ASGIConnection[Any, Any, Any, Any] | None = None,
) -> AsyncGenerator[tuple[Any, ...]]:
    """
    提供多个共享同一个数据库会话的服务。
    用于在 Litestar DI 上下文之外（如后台任务、CLI）获取服务。
    """

    if session is not None and connection is not None:
        raise ValueError("Cannot provide both 'session' and 'connection' - choose one")

    if not providers:
        raise ValueError("At least one service provider is required")

    async def _collect_services(
        db_session: AsyncSession,
    ) -> tuple[tuple[object, ...], list[AsyncGenerator[Any]]]:
        services: list[object] = []
        generators: list[AsyncGenerator[Any]] = []
        try:
            for provider in providers:
                generator = provider(db_session)
                generators.append(generator)
                services.append(await generator.__anext__())
        except Exception:
            for generator in reversed(generators):
                await generator.aclose()
            raise
        return tuple(services), generators

    async def _run(
        db_session: AsyncSession, *, commit: bool
    ) -> AsyncGenerator[tuple[Any, ...]]:
        services, generators = await _collect_services(db_session)
        try:
            yield services
        finally:
            for generator in reversed(generators):
                await generator.aclose()
            if commit:
                await db_session.commit()

    if session is not None:
        async for value in _run(session, commit=False):
            yield value

    elif connection is not None:
        db_session = sqlalchemy_config.provide_session(
            connection.app.state, connection.scope
        )

        async for value in _run(db_session, commit=False):
            yield value

    else:
        session_maker = sqlalchemy_config.create_session_maker()
        db_session = session_maker()

        async with db_session:
            async for value in _run(db_session, commit=True):
                yield value
