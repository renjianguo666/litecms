"""设置字段注册器

各模块通过 SettingRegistry.register() 声明自己的配置项,
表单自动生成结构化字段,模板变量区留给模板用的自定义变量。

类似 PermissionGuard 的自动注册模式。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Literal

FieldType = Literal["text", "number", "textarea", "list", "boolean"]


@dataclass(frozen=True)
class SettingField:
    """一个可配置项的声明

    group 只用于表单 UI 分块展示,不写入 TOML section。
    """

    key: str
    label: str
    field_type: FieldType = "text"
    default: Any = ""
    description: str = ""
    group: str = "其他"
    # False: 系统设置表单不渲染该字段(由模块自定义渲染, 如 themes 的切换按钮)。
    # 仍注册进体系: 保存/读取统一处理, 且注册 key 自然不进模板变量区。
    render_in_settings: bool = True


class SettingRegistry:
    """配置项注册器,各模块 import 并声明字段"""

    _fields: ClassVar[list[SettingField]] = []

    @classmethod
    def register(cls, field: SettingField) -> None:
        if not any(f.key == field.key for f in cls._fields):
            cls._fields.append(field)

    @classmethod
    def fields(cls) -> list[SettingField]:
        return list(cls._fields)

    @classmethod
    def keys(cls) -> set[str]:
        return {f.key for f in cls._fields}

    @classmethod
    def defaults(cls) -> dict[str, Any]:
        return {f.key: f.default for f in cls._fields}

    @classmethod
    def grouped(cls) -> dict[str, list[SettingField]]:
        """按 group 分组,保持注册顺序。render_in_settings=False 的字段不进分组
        (设置表单不渲染, 模块自定义渲染)。"""
        groups: dict[str, list[SettingField]] = {}
        for f in cls._fields:
            if not f.render_in_settings:
                continue
            groups.setdefault(f.group, []).append(f)
        return groups
