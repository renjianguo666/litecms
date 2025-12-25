from __future__ import annotations

from functools import cached_property

from .exceptions import ExceptionConfig, create_exception_handlers
from .middleware import create_middleware_config
from .openapi import OpenAPIConfig, create_openapi_config
from .settings import Settings
from .sqlalchemy import SQLAlchemyAsyncConfig, create_sqlalchemy_config
from .stores import StoreRegistry, create_stores_config
from .structlog import StructlogConfig, create_structlog_config
from .template import TemplateConfig, create_template_config


class PluginRegistry:
    """
    插件注册表：专门存放构造好的复杂对象 (Factories)
    这里面存放的都是 '对象' (Objects)，而不是原始配置数据
    """

    def __init__(self, settings: Settings) -> None:
        # 持有配置的引用，以便工厂函数使用
        self._settings = settings

    @cached_property
    def sqlalchemy(self) -> SQLAlchemyAsyncConfig:
        """SQLAlchemy 插件配置对象"""
        return create_sqlalchemy_config(self._settings)

    @cached_property
    def structlog(self) -> StructlogConfig:
        """日志插件配置对象"""
        return create_structlog_config(self._settings)

    @cached_property
    def stores(self) -> StoreRegistry:
        """缓存存储注册表对象"""
        return create_stores_config(self._settings)

    @cached_property
    def openapi(self) -> OpenAPIConfig:
        """OpenAPI 文档配置对象"""
        return create_openapi_config(self._settings)

    @cached_property
    def template(self) -> TemplateConfig:
        """模板引擎配置对象"""
        return create_template_config(self._settings)

    @cached_property
    def middleware(self) -> list:
        """中间件列表"""
        return create_middleware_config(self._settings)

    @cached_property
    def exception_handlers(self) -> ExceptionConfig:
        """异常处理器字典"""
        return create_exception_handlers()


class Config(Settings):
    @cached_property
    def plugins(self) -> PluginRegistry:
        return PluginRegistry(self)


config = Config()
