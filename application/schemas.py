from __future__ import annotations

from datetime import datetime
from typing import get_args

import msgspec
from msgspec.structs import fields as struct_fields

from application.config import cfg


class Schema(msgspec.Struct):
    """所有展示层 Schema 的基类。

    通过 msgspec.convert(obj, SchemaCls, from_attributes=True) 把
    ORM 模型转为 Schema 时，convert 路径会触发 __post_init__，
    统一做归一，供 Jinja2 模板直接输出，无需模板侧判断：
    1. 直出型字段(str/datetime 可空)None → 空串，模板直出不出现 "None"；
       int/UUID/bool 等业务字段保持 None，类型与可空语义不受影响
    2. aware datetime → 本地 naive

    子类只需声明字段，无需重写任何方法。
    """

    def __post_init__(self) -> None:
        for fi in struct_fields(type(self)):
            val = getattr(self, fi.name)
            if val is None:
                if str in get_args(fi.type) or datetime in get_args(fi.type):
                    setattr(self, fi.name, "")
                continue
            if isinstance(val, datetime) and val.tzinfo is not None:
                setattr(
                    self,
                    fi.name,
                    val.astimezone(cfg.tzinfo).replace(tzinfo=None, microsecond=0),
                )
