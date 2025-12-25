from litestar import Litestar
from litestar.config.response_cache import ResponseCacheConfig
from litestar.di import Provide
from litestar.plugins.sqlalchemy import SQLAlchemyPlugin
from litestar.plugins.structlog import StructlogPlugin

from .commands import CommandPlugin
from .config import config
from .deps import provide_limit_offset
from .router import route_handlers
from .security import SecurityPlugin
from .web import events

__all__ = ["create_app"]


def create_app():
    return Litestar(
        route_handlers=route_handlers,
        plugins=[
            StructlogPlugin(config=config.plugins.structlog),
            SQLAlchemyPlugin(config=config.plugins.sqlalchemy),
            SecurityPlugin(),
            CommandPlugin(),
        ],
        dependencies={
            "limit_offset": Provide(provide_limit_offset, sync_to_thread=False)
        },
        response_cache_config=ResponseCacheConfig(store="default"),
        middleware=config.plugins.middleware,
        stores=config.plugins.stores,
        template_config=config.plugins.template,
        openapi_config=config.plugins.openapi,
        exception_handlers=config.plugins.exception_handlers,
        listeners=[
            events.on_category_changed,
            events.on_feature_changed,
            events.on_special_changed,
        ],
    )
