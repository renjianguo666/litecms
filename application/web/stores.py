from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.stores.memory import MemoryStore
from pydantic import TypeAdapter

from application.taxonomies.schemas import (
    CategoryLiteSchema,
    FeatureLiteSchema,
    SpecialLiteSchema,
)
from application.taxonomies.services import (
    CategoryRepository,
    FeatureRepository,
    SpecialRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


CATEGORIES_CACHE_KEY = "categories"
SPECIALS_CACHE_KEY = "specials"
FEATURES_CACHE_KEY = "features"

store = MemoryStore()

# ==========================================
# 定义列表类型的适配器 (Pydantic V2 核心)
# ==========================================
# 用于处理 list[Schema] 的序列化、反序列化和 ORM 转换
category_list_adapter = TypeAdapter(list[CategoryLiteSchema])
feature_list_adapter = TypeAdapter(list[FeatureLiteSchema])
special_list_adapter = TypeAdapter(list[SpecialLiteSchema])


async def get_categories_cached(session: AsyncSession) -> list[CategoryLiteSchema]:
    cached = await store.get(CATEGORIES_CACHE_KEY)
    if cached is not None:
        # Pydantic V2: 使用适配器反序列化列表
        return category_list_adapter.validate_json(cached)

    repo = CategoryRepository(session=session)
    result = await repo.list(order_by=[("trail", False)])

    categories = category_list_adapter.validate_python(result)

    await store.set(CATEGORIES_CACHE_KEY, category_list_adapter.dump_json(categories))

    return categories


async def get_features_cached(session: AsyncSession) -> list[FeatureLiteSchema]:
    cached = await store.get(FEATURES_CACHE_KEY)
    if cached is not None:
        return feature_list_adapter.validate_json(cached)

    repo = FeatureRepository(session=session)
    result = await repo.list()

    features = feature_list_adapter.validate_python(result)

    await store.set(FEATURES_CACHE_KEY, feature_list_adapter.dump_json(features))
    return features


async def get_specials_cached(session: AsyncSession) -> list[SpecialLiteSchema]:
    cached = await store.get(SPECIALS_CACHE_KEY)
    if cached is not None:
        return special_list_adapter.validate_json(cached)

    repo = SpecialRepository(session=session)
    result = await repo.list()

    specials = special_list_adapter.validate_python(result)

    await store.set(SPECIALS_CACHE_KEY, special_list_adapter.dump_json(specials))
    return specials
