from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Mapping
from uuid import UUID

from advanced_alchemy.filters import (
    CollectionFilter,
    ComparisonFilter,
    ExistsFilter,
    LimitOffset,
    OrderBy,
)

from application.articles.models import Article, PublishStatus
from application.articles.services import ArticleRepository
from application.config import config, template
from application.taxonomies.models import Feature, Special
from application.utils import list_to_tree

from .schemas import (
    article_list_adapter,
    category_list_adapter,
    feature_list_adapter,
    special_list_adapter,
)
from .stores import (
    get_categories_cached,
    get_features_cached,
    get_specials_cached,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def get_session_by_request(ctx: Mapping[str, Any]) -> AsyncSession:
    request = ctx.get("request")
    if request is None:
        raise KeyError("模板上下文中缺少 'request' 对象")
    return config.plugins.sqlalchemy.provide_session(request.app.state, request.scope)


@template.global_function(use_context=True)
async def categories_tree(ctx):
    result = await get_categories_cached(get_session_by_request(ctx))
    pydantic_list = category_list_adapter.validate_python(result)
    return list_to_tree(category_list_adapter.dump_python(pydantic_list))


@template.global_function(use_context=True)
async def categories(ctx):
    result = await get_categories_cached(get_session_by_request(ctx))
    pydantic_list = category_list_adapter.validate_python(result)
    return category_list_adapter.dump_python(pydantic_list)


@template.global_function(use_context=True)
async def specials(ctx):
    result = await get_specials_cached(get_session_by_request(ctx))
    pydantic_list = special_list_adapter.validate_python(result)
    return special_list_adapter.dump_python(pydantic_list)


@template.global_function(use_context=True)
async def features(ctx):
    result = await get_features_cached(get_session_by_request(ctx))
    pydantic_list = feature_list_adapter.validate_python(result)
    return feature_list_adapter.dump_python(pydantic_list)


@template.global_function(use_context=True)
async def feature_select(ctx, *args):
    features = await get_features_cached(get_session_by_request(ctx))
    if args:
        features = [feature for feature in features if feature.id in args]
    pydantic_list = feature_list_adapter.validate_python(features)
    return feature_list_adapter.dump_python(pydantic_list)


@template.global_function(use_context=True)
async def special_select(ctx, *args):
    specials = await get_specials_cached(get_session_by_request(ctx))
    if args:
        specials = [special for special in specials if special.id in args]

    pydantic_list = special_list_adapter.validate_python(specials)
    return special_list_adapter.dump_python(pydantic_list)


@template.global_function(use_context=True)
async def category_select(ctx, *args):
    """
    获取栏目

    Args:
        ctx (Context): The context object.
        *args: Variable length argument list.
            id (UUID): The ID of the category.
            如果指定了id，则返回指定的栏目，否则返回所有栏目。

    Returns:
        list: List of selected categories.
    """
    categories = await get_categories_cached(get_session_by_request(ctx))
    if args:
        categories = [category for category in categories if category.id in args]

    pydantic_list = category_list_adapter.validate_python(categories)
    return category_list_adapter.dump_python(pydantic_list)


@template.global_function(use_context=True)
async def article_select(
    ctx,
    category: UUID | list[UUID] | None = None,
    special: UUID | list[UUID] | None = None,
    feature: UUID | list[UUID] | None = None,
    limit: int = 10,
    order_by: str = "published_at",
    order_dir: Literal["desc", "asc"] = "desc",
):
    repo = ArticleRepository(session=get_session_by_request(ctx))

    condition = [
        OrderBy(field_name=order_by, sort_order=order_dir),
        LimitOffset(limit=limit, offset=0),
        ComparisonFilter(
            field_name="status", operator="eq", value=PublishStatus.PUBLISHED
        ),
    ]

    # 处理 category 参数
    if category is not None:
        if isinstance(category, list):
            condition.append(
                CollectionFilter(field_name="category_id", values=category)
            )
        else:
            condition.append(
                ComparisonFilter(
                    field_name="category_id", operator="eq", value=category
                )
            )

    # 处理 special 参数
    if special is not None:
        if isinstance(special, list):
            condition.append(
                ExistsFilter([Article.specials.any(Special.id.in_(special))])
            )
        else:
            condition.append(Article.specials.any(Special.id == special))

    # 处理 feature 参数
    if feature is not None:
        if isinstance(feature, list):
            condition.append(
                ExistsFilter([Article.features.any(Feature.id.in_(feature))])
            )
        else:
            condition.append(Article.features.any(Feature.id == feature))

    result = await repo.list(*condition)
    pydantic_list = article_list_adapter.validate_python(result)
    return article_list_adapter.dump_python(pydantic_list)
