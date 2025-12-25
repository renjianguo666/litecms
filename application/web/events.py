from litestar.events import listener

from .stores import CATEGORIES_CACHE_KEY, FEATURES_CACHE_KEY, SPECIALS_CACHE_KEY, store


@listener("category_changed")
async def on_category_changed(**kwargs):
    await store.delete(CATEGORIES_CACHE_KEY)


@listener("feature_changed")
async def on_feature_changed(**kwargs):
    await store.delete(FEATURES_CACHE_KEY)


@listener("special_changed")
async def on_special_changed(**kwargs):
    await store.delete(SPECIALS_CACHE_KEY)
