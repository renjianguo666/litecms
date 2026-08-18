from __future__ import annotations

from wtforms import Form, RadioField, SubmitField, TextAreaField
from wtforms.validators import StopValidation

from application.settings import SettingField, SettingRegistry

# 注册 SEO 配置字段(模块导入即注册, 类似 PermissionGuard):
# 在系统设置页生成结构化字段, 并从模板变量区(textarea)排除
SettingRegistry.register(
    SettingField(
        key="sitemap_enabled",
        label="启用 Sitemap",
        field_type="boolean",
        default=True,
        description="生成 /sitemap.xml,供 360/搜狗/头条等站长平台配置",
        group="SEO",
    )
)
SettingRegistry.register(
    SettingField(
        key="baidu_push_sites",
        label="百度推送站点与 Token",
        field_type="textarea",
        default="",
        description="每行一个站点，格式: 站点URL|Token，例如 https://www.abc.com|xxxxx；"
        "可配置多行支持多站点，推送时按 URL 主机匹配对应 Token；"
        "Token 在百度站长平台「普通收录」获取。",
        group="SEO",
    )
)


class URLListField(TextAreaField):
    """每行一个 URL 的文本域; .parsed 为去空后的 URL 列表, .data 保留原文本。

    解析下沉到字段级: form.validate() 通过后 form.urls.parsed 直接是 [url, ...];
    空则由 validate_urls 抛错, 走 WTForms render_errors 展示。
    .data 保留原始文本(沿用父类, 不覆盖类型避免冲突), textarea 显示原样不被清理。
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # WTForms __init__ 把 type 设为类名("URLListField"),
        # 改回 "TextAreaField" 让共享 render_field 宏按文本域渲染。
        self.type = "TextAreaField"

    @staticmethod
    def _parse(raw: str) -> list[str]:
        return [u.strip() for u in (raw or "").splitlines() if u.strip()]

    @property
    def parsed(self) -> list[str]:
        return self._parse(self.data or "")


class PushForm(Form):
    """手动推送表单: 每行一个 URL, 用于栏目/专题/单页等非文章链接"""

    urls = URLListField(
        "推送链接",
        default="",
        description="每行一个 URL，可补充栏目 / 专题 / 单页等任意链接；"
        "可输入多个站点的链接，按主机匹配对应 Token 推送，未配置站点的链接自动跳过",
        render_kw={"rows": "8", "placeholder": "https://example.com/article/1"},
    )
    action = RadioField(
        "如何处理重复项",
        choices=[("skip", "跳过重复（只推新的）"), ("force", "强制推送（含重复项全部重推）")],
        default=None,
        validate_choice=False,
    )
    submit = SubmitField("确认推送")

    def validate_urls(self, field) -> None:
        if not field.parsed:
            raise StopValidation("请输入至少一个 URL")
