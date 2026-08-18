"""前台共享数据缓存 (基于 Litestar FileStore)。

categories (全站栏目导航) 缓存: base.html 高频调用 (导航 3 次 + 页脚),
树结构重, 全量缓存收益大。tags/specials/features 数据小、调用少, 不缓存。

缓存失效靠手动 delete (后台增删改栏目后调用 invalidate_categories)。
无 TTL、无 mtime、无内存缓存——FileStore 每次读盘, OS page cache 兜底。
"""

from __future__ import annotations

import msgspec
from litestar.stores.base import Store
from msgspec import convert
from sqlalchemy.ext.asyncio import AsyncSession

from application.config import cfg
from application.taxonomies.schemas import CategorySchema
from application.taxonomies.services import CategoryService

_CACHE_KEY = "all"


def _store() -> Store:
    """获取 categories 命名空间的 FileStore (由 StoreRegistry 自动创建)。"""
    return cfg.stores.get("categories")


async def get_categories_cached(session: AsyncSession) -> list[CategorySchema]:
    """全量栏目 (按 trail 升序), 统一返回 CategorySchema 列表。

    cache miss → 查库 → msgpack 序列化 → 写 FileStore;
    cache hit → msgpack 反序列化返回。
    """
    store = _store()
    raw = await store.get(_CACHE_KEY)
    if raw is not None:
        return msgspec.msgpack.decode(raw, type=list[CategorySchema])

    data = convert(
        await CategoryService(session=session).get_many(order_by=[("trail", False)]),
        list[CategorySchema],
        from_attributes=True,
    )
    await store.set(_CACHE_KEY, msgspec.msgpack.encode(data))
    return data


async def invalidate_categories() -> None:
    """删除栏目缓存 → 下次读取自动查库重建。

    后台增删改栏目后调用。删文件而非重写: 避免竞态
    (后台事务还没提交就写缓存会读到旧数据), 让下次读取时数据库已提交。
    """
    await _store().delete(_CACHE_KEY)
