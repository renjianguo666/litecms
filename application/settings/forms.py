"""系统设置表单"""

from __future__ import annotations

import tomllib
from typing import Any

from wtforms import (
    BooleanField,
    Form,
    IntegerField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import StopValidation

from application.settings.fields import SettingField, SettingRegistry
from application.settings.manager import get_free_text, save_settings


def _create_field(f: SettingField, value: Any | None = None):
    """根据 SettingField 创建 wtforms 字段"""
    default = value if value is not None else f.default
    if f.field_type == "list" and isinstance(default, list):
        default = ", ".join(default)

    common = {"label": f.label, "description": f.description, "default": default}

    if f.field_type == "number":
        return IntegerField(
            **common, render_kw={"class": "input input-bordered w-full"}
        )
    if f.field_type == "textarea":
        return TextAreaField(
            **common,
            render_kw={
                "class": "textarea textarea-bordered w-full font-mono text-sm",
                "rows": 4,
            },
        )
    if f.field_type == "boolean":
        return BooleanField(**common, render_kw={"class": "checkbox checkbox-neutral"})
    return StringField(**common, render_kw={"class": "input input-bordered w-full"})


class SettingFormBase(Form):
    """设置表单基类。

    submit 是固定字段;template_vars 的实际字段实例由 create_setting_form() 注入,
    此处仅声明类型供类型检查器识别。
    save / validate_template_vars 是固定方法,不随注册字段变化。
    """

    submit = SubmitField("保存设置", render_kw={"class": "btn btn-neutral"})
    template_vars: TextAreaField

    def validate_template_vars(self, field) -> None:
        text = (field.data or "").strip()
        if not text:
            return
        try:
            tomllib.loads(text)
        except tomllib.TOMLDecodeError as e:
            raise StopValidation(f"TOML 语法错误: {e}")

    def save(self) -> None:
        registered: dict[str, Any] = {}
        for f in SettingRegistry.fields():
            val = getattr(self, f.key).data
            if f.field_type == "list" and isinstance(val, str):
                val = [s.strip() for s in val.split(",") if s.strip()]
            registered[f.key] = val
        save_settings(registered, getattr(self, "template_vars").data or "")


def create_setting_form() -> type[SettingFormBase]:
    """动态构建设置表单类。每次请求调用,确保拿到最新注册字段和当前值。"""
    from application.settings.manager import load_settings

    settings = load_settings()
    attrs: dict[str, Any] = {}

    for f in SettingRegistry.fields():
        attrs[f.key] = _create_field(f, settings.get(f.key))

    attrs["template_vars"] = TextAreaField(
        "模板变量",
        description="TOML 格式,模板中通过 settings.变量名 使用。备案号、联系邮箱、SEO关键词等站点自定义配置写在这里。",
        default=get_free_text(),
        render_kw={
            "rows": 10,
            "class": "textarea textarea-bordered w-full font-mono text-sm",
            "placeholder": 'site_icp = "京ICP备123456号"\ncontact_email = "admin@example.com"\nsite_keywords = "博客, 技术, 分享"\nfooter_copyright = "© 2026 我的博客"',
        },
    )

    return type("SettingForm", (SettingFormBase,), attrs)
