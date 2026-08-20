from __future__ import annotations

import hashlib
import re
from datetime import datetime
from os.path import splitext
from typing import TYPE_CHECKING
from uuid import UUID

from application.config import cfg

if TYPE_CHECKING:
    from application.contents.models import Content
    from application.taxonomies.models import Category

# Base31 字母表（去掉 0/1/i/l/o 避免视觉混淆）
ALPHABET = "23456789abcdefghjkmnpqrstuvwxyz"
DEFAULT_KEY_SIZE = 12
DEFAULT_NUM_SIZE = 8
_GEN_LENGTH = 24

_PLACEHOLDER_RE = re.compile(r"\{([^}]+)\}")


def uuid_to_base31(uuid_val: UUID) -> str:
    """UUID → 24 位 Base31 字符串（SHA-256 提供足够熵）。"""
    h = hashlib.sha256(uuid_val.bytes).digest()
    num = int.from_bytes(h, "big")
    chars: list[str] = []
    while len(chars) < _GEN_LENGTH:
        num, rem = divmod(num, 31)
        chars.append(ALPHABET[rem])
    return "".join(reversed(chars))


def uuid_to_num(uuid_val: UUID) -> str:
    """UUID → 24 位数字字符串。"""
    return str(uuid_val.int % (10**_GEN_LENGTH)).zfill(_GEN_LENGTH)


def build_permalink(rule: str, model: Category | Content) -> str:
    """
    根据 URL 规则 + 模型对象生成路径。

    占位符:
        {key}      UUID → Base31，默认取前 12 位
        {key:N}    取前 N 位（正数）或后 N 位（负数）
        {num}      UUID → 数字，默认取后 8 位（随机熵在低位）
        {num:N}    取后 N 位（正负数均从结尾取，高位被时间戳主导、碰撞率高）
        {parent}   model.parent.path（去扩展名）
        {category} model.category.path（去扩展名）
        {year}     四位年份
        {yy}       两位年份
        {month}    月份（不补零）
        {mm}       月份（补零）
        {day}      日（不补零）
        {dd}       日（补零）
    """
    dt: datetime = (
        getattr(model, "published_at", None) or getattr(model, "created_at", None) or datetime.now(cfg.tzinfo)
    )

    ctx: dict[str, str] = {
        "key": uuid_to_base31(model.id),
        "num": uuid_to_num(model.id),
        "year": str(dt.year),
        "yy": dt.strftime("%y"),
        "month": str(dt.month),
        "mm": dt.strftime("%m"),
        "day": str(dt.day),
        "dd": dt.strftime("%d"),
    }

    category = getattr(model, "category", None)
    if category is not None:
        ctx["category"] = splitext(category.path)[0]

    parent = getattr(model, "parent", None)
    if parent is not None:
        ctx["parent"] = splitext(parent.path)[0] if parent.path else ""

    def replacer(match: re.Match[str]) -> str:
        name, _, length_str = match.group(1).partition(":")
        val = ctx.get(name, "")
        if length_str:
            try:
                n = int(length_str)
            except ValueError:
                return val
            if n > 0:
                # num 的随机熵在低位（高位被时间戳主导），正数同样取后缀
                return val[-n:] if name == "num" else val[:n]
            return val[n:]

        if name == "key":
            return val[:DEFAULT_KEY_SIZE]
        if name == "num":
            return val[-DEFAULT_NUM_SIZE:]
        return val

    return _PLACEHOLDER_RE.sub(replacer, rule)
