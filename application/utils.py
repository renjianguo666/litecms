from __future__ import annotations

import random
import re
import string
from datetime import datetime
from functools import lru_cache
from typing import Any, Union
from uuid import UUID

import msgspec
from fastnanoid import generate
from litestar.utils.path import normalize_path

# 占位符 正则
PLACEHOLDER_RE = re.compile(r"\{([^}]+)\}")
# 默认 Base32 字母表 (去掉了 '1', 'i', 'o', '0' 避免混淆
DEFAULT_ALPHABET = "23456789abcdefghjklmnpqrstuvwxyz"


@lru_cache
def settings() -> dict[str, Any]:
    from application.config import config

    _settings_file = config.app_dir / "settings.yaml"
    if _settings_file.exists():
        with open(_settings_file, "r") as f:
            return msgspec.yaml.decode(f.read())
    return {}


@lru_cache(maxsize=32)
def _get_decode_map(alphabet: str) -> dict[str, int]:
    """
    构建解码查找表 (带缓存)
    只要 alphabet 参数一样，这个函数只会执行一次
    给short_to_uuid函数用户
    """
    return {char: index for index, char in enumerate(alphabet)}


def uuid_to_short(
    uuid_obj: Union[UUID, str, Any], alphabet: str = DEFAULT_ALPHABET
) -> str:
    """
    将 UUID 转为短字符串。
    优化：针对 Base32 (长度32) 使用位运算加速。
    兼容：支持 uuid.UUID, uuid_utils.UUID 以及 str 类型的 UUID。
    """

    # 1. 统一转换为整数
    try:
        if isinstance(uuid_obj, str):
            number = int(uuid_obj.replace("-", ""), 16)
        elif hasattr(uuid_obj, "bytes"):
            number = int.from_bytes(uuid_obj.bytes, "big")
        else:
            number = int(str(uuid_obj).replace("-", ""), 16)
    except ValueError:
        raise ValueError(f"Invalid UUID input: {uuid_obj}")

    if number == 0:
        return alphabet[0]

    output = []
    base = len(alphabet)

    # 2. 核心转换：Base32 用位运算加速
    if base == 32:
        mask = 31  # 0b11111
        while number:
            output.append(alphabet[number & mask])
            number >>= 5
    else:
        while number:
            number, rem = divmod(number, base)
            output.append(alphabet[rem])

    return "".join(output[::-1])


def short_to_uuid(short_str: str, alphabet: str = DEFAULT_ALPHABET) -> UUID:
    """
    短字符串 -> 标准 UUID 对象
    必须传入与编码时完全一致的 alphabet
    """
    decode_map = _get_decode_map(alphabet)
    base = len(alphabet)

    number = 0
    for char in short_str:
        if char not in decode_map:
            raise ValueError(f"Invalid character '{char}' for the given alphabet.")
        number = number * base + decode_map[char]

    return UUID(int=number)


def list_to_tree(
    items: list[dict],
    id_key: str = "id",
    parent_key: str = "parent_id",
    children_key: str = "children",
) -> list[dict]:
    """
    将扁平字典列表转换为树形结构

    Args:
        items: 扁平的字典列表
        id_key: 节点 ID 的字段名
        parent_key: 父节点 ID 的字段名
        children_key: 子节点列表的字段名

    Returns:
        树形结构的字典列表
    """
    # 构建 id -> node 的映射
    node_map = {item[id_key]: {**item, children_key: []} for item in items}

    # 构建树
    tree = []
    for item_id, node in node_map.items():
        parent_id = node.get(parent_key)
        if parent_id is None:
            tree.append(node)
        elif parent_id in node_map:
            node_map[parent_id][children_key].append(node)

    return tree


def random_number(length: int = 9) -> int:
    """生成指定长度的随机数字（首位不为0）"""
    length = min(length, 9)  # 限制最大长度
    first = random.choice("123456789")
    rest = "".join(random.choices(string.digits, k=length - 1))
    return int(first + rest)


def random_string(length: int = 12) -> str:
    """生成指定长度的随机字符串（小写字母+数字）"""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def build_permalink(rule: str, dt: datetime | None = None, **kwargs) -> str:
    """
    生成 permalink
    支持 {var}, {var:N} (前N字符), {var:-N} (后N字符)

    Args:
        rule: permalink 模板规则
        dt: 日期时间对象（可选，不传则使用当前时间）
        **kwargs: 数据字段，支持:
            - key: UUID (自动转换为 short id)
            - category: 分类路径
            - random_number: 随机数字（可选，不传则自动生成）
            - random_string: 随机字符串（可选，不传则自动生成）
    """
    dt = dt or datetime.now()

    # 附件 key 字段
    if "key" in kwargs:
        kwargs["key"] = generate(alphabet="23456789abcdefghjklmnpqrstuvwxyz")

    # 处理日期时间字段
    kwargs.setdefault("year", dt.year)
    kwargs.setdefault("month", dt.month)
    kwargs.setdefault("day", dt.day)
    kwargs.setdefault("yy", dt.strftime("%y"))
    kwargs.setdefault("mm", dt.strftime("%m"))
    kwargs.setdefault("dd", dt.strftime("%d"))

    # 处理随机字段（懒加载）
    kwargs.setdefault("random_number", random_number())
    kwargs.setdefault("random_string", random_string())

    # 替换占位符
    def replacer(match):
        placeholder = match.group(1)
        key, _, length_str = placeholder.partition(":")

        val = str(kwargs.get(key, ""))

        if length_str:
            try:
                n = int(length_str)
                return val[:n] if n >= 0 else val[n:]
            except ValueError:
                pass
        return val

    permalink = PLACEHOLDER_RE.sub(replacer, rule)

    return normalize_path(permalink)
