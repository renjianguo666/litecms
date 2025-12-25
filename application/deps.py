from __future__ import annotations

from typing import Type, TypeVar

# from typing import Annotated
from advanced_alchemy.extensions.litestar.providers import (
    DependencyCache,
    DependencyDefaults,
    create_filter_dependencies,
    create_service_dependencies,
    create_service_provider,
    dep_cache,
)
from advanced_alchemy.filters import LimitOffset
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from litestar.di import Provide
from litestar.params import Parameter
from sqlalchemy.ext.asyncio import AsyncSession

__all__ = (
    "DependencyCache",
    "DependencyDefaults",
    "create_filter_dependencies",
    "create_service_dependencies",
    "create_service_provider",
    "dep_cache",
    "provide_limit_offset",
)


T = TypeVar("T", bound=SQLAlchemyAsyncRepository)


def create_repo_provider(repo_class: Type[T]) -> Provide:
    async def _repo_provider(db_session: AsyncSession) -> T:
        return repo_class(session=db_session)

    return Provide(_repo_provider)


def provide_limit_offset(
    page: int = Parameter(query="page", ge=1, default=1, required=False),
    page_size: int = Parameter(
        query="page_size", ge=1, le=100, default=10, required=False
    ),
) -> LimitOffset:
    """分页参数依赖注入

    Parameters
    ----------
    page : int
        当前页码，从 1 开始
    page_size : int
        每页数量，默认 10，最大 100

    Returns
    -------
    LimitOffset
        用于 Repository 的分页过滤器
    """
    return LimitOffset(limit=page_size, offset=page_size * (page - 1))
