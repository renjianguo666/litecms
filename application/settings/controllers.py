"""系统设置控制器"""

from __future__ import annotations

from litestar import Controller, get, post
from litestar.datastructures.multi_dicts import FormMultiDict
from litestar.params import URLEncodedBody
from litestar.response import Response, Template

from application.guards import PermissionGuard
from application.htmx import HTMXMixin
from application.settings.fields import SettingRegistry
from application.settings.forms import SettingFormBase, create_setting_form

view_permission = PermissionGuard("settings:view", "查看设置", "系统设置")
save_permission = PermissionGuard("settings:save", "保存设置", "系统设置")


class SettingController(HTMXMixin, Controller):
    """系统设置管理"""

    path = "/settings"

    @get(name="settings:index", guards=[view_permission])
    async def index(self) -> Template:
        """系统设置页面"""
        form_class = create_setting_form()
        form: SettingFormBase = form_class()
        return self.htmx_render(
            template_name="settings.html.j2",
            context={"form": form, "groups": SettingRegistry.grouped()},
        )

    @post(name="settings:save", guards=[save_permission])
    async def save(self, data: URLEncodedBody[FormMultiDict]) -> Response | Template:
        """保存系统设置"""
        form_class = create_setting_form()
        form: SettingFormBase = form_class(formdata=data)
        if form.validate():
            form.save()
            return self.htmx_success("设置保存成功", redirect=data.get("url"))
        return self.htmx_render(
            template_name="settings.html.j2",
            context={"form": form, "groups": SettingRegistry.grouped()},
        )
