from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.openapi import OpenAPIConfig

if TYPE_CHECKING:
    from .settings import Settings


def create_openapi_config(settings: Settings) -> OpenAPIConfig:
    return OpenAPIConfig(
        title="CMS API",
        version="1.0.0",
        description="内容管理系统 API 文档",
        path=settings.api_docs_path,
    )
