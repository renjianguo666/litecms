"""栏目面包屑助手: 从全量栏目缓存解析祖先链。

数据源为 get_categories_cached 的全量列表 (零 DB), 纯同步函数,
调用方取一次缓存后可对多行数据循环解析, 无 N+1、无重复读缓存。
"""

from __future__ import annotations

from uuid import UUID

from .schemas import CategorySchema


def resolve_breadcrumbs(
    categories: list[CategorySchema],
    category_id: UUID | str | None = None,
    trail: str | None = None,
) -> list[CategorySchema]:
    """栏目 id 或 trail(id 链) → 祖先栏目列表(父→子)。

    category_id: 按栏目 id 取该栏目的祖先链;
    trail: 直接传 id 链 ("父.子.孙");
    二选一, 都传时优先 trail; 都不传返回空列表。
    链上查不到的段跳过, 不影响其余祖先。
    """
    if not categories:
        return []

    by_id = {str(c.id): c for c in categories}

    if not trail and category_id is not None:
        cat = by_id.get(str(category_id))
        if cat is not None:
            trail = cat.trail

    if not trail:
        return []

    return [by_id[seg] for seg in trail.split(".") if seg in by_id]
