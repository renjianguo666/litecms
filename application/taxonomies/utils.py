import re
from collections import defaultdict
from typing import Any
from urllib.parse import quote
from uuid import UUID

RE_CONSECUTIVE_SLASHES = re.compile(r"/+")  # 连续斜杠
URL_PLACEHOLDERS = {
    "{id}": "__ID__",
    "{slug}": "__SLUG__",
    "{year}": "__YEAR__",
    "{month}": "__MONTH__",
    "{day}": "__DAY__",
    "{category}": "__CAT__",
}
# 反向映射
REVERSE_URL_PLACEHOLDERS = {v: k for k, v in URL_PLACEHOLDERS.items()}

CATEGORY_PARAMS = defaultdict(
    str,
    id="(?P<id>[1-9][0-9]{0,9}|214748364[0-7])",
    key="(?P<key>[23456789abcdefghjklmnpqrstuvwxyz]{8})",
    page="(?P<page>[0-9])",
)
ENTRY_PARAMS = defaultdict(
    str,
    id="(?P<id>[1-9][0-9]{0,9}|214748364[0-7])",
    key="(?P<key>[23456789abcdefghjklmnpqrstuvwxyz]{18})",
    year="(?P<year>[0-9]{4})",
    month="(?P<month>[0-9]{2})",
    day="(?P<day>[0-9]{2})",
)


def normalize_url_pattern(url_pattern: str) -> str:
    pattern = url_pattern.strip().lstrip("/")

    # 2. 保护占位符 (Masking)
    # 将 {id} 替换为 __ID__，防止被 quote 编码
    for original, temp_token in URL_PLACEHOLDERS.items():
        pattern = pattern.replace(original, temp_token)

    # 3. URL 编码 (Encoding)
    # 对路径中的中文或特殊符号编码，保留 / : . - _
    pattern = quote(pattern, safe="/:.-_")

    # 4. 恢复占位符 (Unmasking)
    for temp_token, original in REVERSE_URL_PLACEHOLDERS.items():
        pattern = pattern.replace(temp_token, original)

    return RE_CONSECUTIVE_SLASHES.sub("/", pattern)


def render_url(pattern, context):
    return pattern.format_map(context)


def build_site_category_trees(
    flat_data: list[dict[str, Any]],
) -> dict[UUID, list[dict[str, Any]]]:
    """
    将扁平的 Category 数据字典列表，按 site_id 分组并构建树结构。

    Args:
        flat_data: 从 ORM 对象转换而来的 Category 字典列表 (必须包含 site_id 和 parent_id)。

    Returns:
        Dict[UUID, List[Dict]]: 键为 Site ID，值为该站点下的根 Category 列表。
    """

    # 1. 映射所有节点 ID 和初始化 children 列表
    # id_map: 存储所有节点对象，用于 O(1) 查找父节点
    id_map: dict[UUID, dict[str, Any]] = {}

    # site_root_map: 存储最终结果，键是 site_id，值为该站点的根节点列表
    site_root_map: dict[UUID, list[dict[str, Any]]] = {}

    for item in flat_data:
        site_id = item["site_id"]

        # 确保 children 列表已初始化
        item["children"] = []
        id_map[item["id"]] = item

        # 确保 site_id 键存在于最终的 Map 中
        if site_id not in site_root_map:
            site_root_map[site_id] = []

    # 2. 遍历并连接节点，同时区分根节点
    for item in flat_data:
        parent_id = item.get("parent_id")
        site_id = item["site_id"]

        if parent_id is None:
            # 根节点：直接添加到对应的 site_id 列表
            site_root_map[site_id].append(item)

        elif parent_id in id_map:
            parent = id_map[parent_id]

            # 确保父节点和子节点属于同一个站点，以防脏数据
            if parent.get("site_id") == site_id:
                parent["children"].append(item)

    # 3. 最终排序 (按 priority 降序)
    for site_id, roots in site_root_map.items():
        # 对每个站点的根节点列表进行排序
        roots.sort(key=lambda c: c.get("priority", 0), reverse=True)

    return site_root_map


def build_category_tree(flat_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    将扁平的 Category 数据字典列表转换为嵌套的树状结构。

    Args:
        flat_data: 从 ORM 对象转换而来的 Category 字典列表 (所有字段都是可变字典)。

    Returns:
        一个列表，包含所有根节点，子节点通过 'children' 键链接。
    """

    # 1. 创建 ID 映射表 (O(1) 查找父节点)
    # 同时初始化 children 列表，防止 linking 失败
    id_map: dict[UUID, dict[str, Any]] = {}
    for item in flat_data:
        # 核心：确保每个节点的 children 列表是干净且可变的
        item["children"] = []
        id_map[item["id"]] = item

    root_categories = []

    # 2. 遍历并连接节点
    for item in flat_data:
        # parent_id 可能是 None，也可能是一个 UUID
        parent_id = item.get("parent_id")

        if parent_id is None:
            # 根节点
            root_categories.append(item)

        elif parent_id in id_map:
            # 子节点：将自己挂载到父节点的 children 列表中
            parent = id_map[parent_id]
            parent["children"].append(item)

        # ⚠️ 注意: 如果 parent_id 存在于 item 中，但不在 id_map 中（例如数据不完整），该节点会被忽略。

    # 3. 对根节点进行排序 (priority 越大越靠前)
    # 我们依赖于 'priority' 字段，降序排列
    root_categories.sort(key=lambda c: c.get("priority", 0), reverse=True)

    return root_categories
