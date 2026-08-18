from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from debug_toolbar.litestar import (
    DebugToolbarPlugin,
    LitestarDebugToolbarConfig,
)
from litestar.plugins.htmx import HTMXPlugin
from litestar.plugins.sqlalchemy import SQLAlchemyPlugin

from application.commands import CommandPlugin
from application.config import cfg
from application.database import sqlalchemy_config
from application.security import SecurityPlugin

if TYPE_CHECKING:
    from debug_toolbar.litestar import DebugToolbarPlugin


class PluginRegistry:
    @cached_property
    def sqlalchemy(self) -> SQLAlchemyPlugin:
        return SQLAlchemyPlugin(config=sqlalchemy_config)

    @cached_property
    def htmx(self) -> HTMXPlugin:
        return HTMXPlugin()

    @cached_property
    def debug_toolbar(self) -> "DebugToolbarPlugin":
        return DebugToolbarPlugin(
            LitestarDebugToolbarConfig(
                enabled=cfg.debug,
                exclude_paths=["/_debug_toolbar", "/static", "/health"],
                max_request_history=50,
                intercept_redirects=False,
                show_toolbar_callback=lambda request: request.app.debug,
                exclude_panels=["VersionsPanel"],
                extra_panels=["debug_toolbar.extras.advanced_alchemy.SQLAlchemyPanel"],
            )
        )

    @cached_property
    def security(self) -> SecurityPlugin:
        return SecurityPlugin()

    @cached_property
    def cli(self) -> CommandPlugin:
        return CommandPlugin()


plugins = PluginRegistry()
