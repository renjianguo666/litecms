from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.middleware.session.server_side import ServerSideSessionConfig

if TYPE_CHECKING:
    from .settings import Settings


def create_middleware_config(settings: Settings):
    return [ServerSideSessionConfig().middleware]
