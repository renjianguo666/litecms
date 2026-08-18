"""系统设置的默认注册字段

模块导入即注册,确保 settings 表单能展示所有系统级配置。
"""

from __future__ import annotations

from application.settings.fields import SettingField, SettingRegistry


def register_defaults() -> None:
    """注册系统级默认配置项"""

    # === 站点 ===
    SettingRegistry.register(
        SettingField(
            key="site_url",
            label="站点 URL",
            field_type="text",
            default="",
            description="[site_url] 站点完整地址,如 https://example.com",
            group="站点",
        )
    )
    SettingRegistry.register(
        SettingField(
            key="site_name",
            label="站点名称",
            field_type="text",
            default="",
            description="[site_name] 网站名称,显示在浏览器标题栏和页头",
            group="站点",
        )
    )
    SettingRegistry.register(
        SettingField(
            key="site_title",
            label="SEO 标题",
            field_type="text",
            default="",
            description="[site_title] 搜索引擎展示用的标题",
            group="站点",
        )
    )
    SettingRegistry.register(
        SettingField(
            key="site_description",
            label="站点描述",
            field_type="textarea",
            default="",
            description="[site_description] 站点描述,用于 SEO meta description",
            group="站点",
        )
    )

