"""栏目层级助手: 同一份扁平 CategorySchema 列表 → 树 / 祖先链。

数据源统一为 get_categories_cached 的全量列表 (零 DB), 纯同步函数,
调用方取一次缓存后可对多行数据循环解析, 无 N+1、无重复读缓存。

build_tree:         扁平列表 → 父子嵌套树 (每节点含 children)
resolve_breadcrumbs: 栏目 id 或 trail → 祖先栏目链 (父→子)
"""

from __future__ import annotations

from collections.abc import Sequence
from copy import copy
from uuid import UUID

from .schemas import CategorySchema

type Tree[T] = list[T]


def build_tree(
    categories: Sequence[CategorySchema],
    root_id: UUID | None = None,
) -> Tree[CategorySchema]:
    """扁平栏目列表 → 父子嵌套树。

    categories: 全量栏目 (CategorySchema, 来自缓存或 ORM convert);
    root_id: 非 None 时只返回以该栏目为根的子树;
    返回根节点列表, 每节点 children 已按输入顺序挂好子孙。
    节点为浅拷贝, 不会污染传入列表的 children。
    """
    if not categories:
        return []

    nodes = [copy(cat) for cat in categories]
    node_dict = {node.id: node for node in nodes}

    # 先统一重置 children (浅拷贝共享原列表, 必须先换新列表再挂接,
    # 避免子节点先于父节点入列时, 父节点的重置把已挂上的子节点清掉)
    for node in nodes:
        node.children = []

    tree: Tree[CategorySchema] = []

    for node in nodes:
        if node.parent_id and node.parent_id in node_dict:
            node_dict[node.parent_id].children.append(node)
        else:
            tree.append(node)

    if root_id is not None:
        return [node_dict[root_id]] if root_id in node_dict else []
    return tree


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
