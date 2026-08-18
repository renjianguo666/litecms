"""系统设置模块 - TOML 文件存储"""

from application.settings.controllers import SettingController

# 注册系统级默认配置(站点信息等)
from application.settings.defaults import register_defaults
from application.settings.fields import SettingField, SettingRegistry
from application.settings.forms import SettingFormBase, create_setting_form
from application.settings.manager import (
    get_free_text,
    get_settings,
    load_settings,
    save_settings,
)

register_defaults()

__all__ = [
    "SettingController",
    "SettingField",
    "SettingFormBase",
    "SettingRegistry",
    "create_setting_form",
    "get_free_text",
    "get_settings",
    "load_settings",
    "save_settings",
]
