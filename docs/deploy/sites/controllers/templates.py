from __future__ import annotations

from typing import Annotated

from litestar import Controller, delete, get, patch, put
from litestar.di import Provide
from litestar.params import Parameter

from application.config import config
from application.guards import PermissionGuard

from ..manager import TemplateManager
from ..schemas import (
    TemplateRenameSchema,
    TemplateContentSchema,
)


# 权限定义
view_permission = PermissionGuard("sites:view_template", "查看模板")
edit_permission = PermissionGuard("sites:edit_template", "编辑模板")
delete_permission = PermissionGuard("sites:delete_template", "删除模板")


def provide_template_manager() -> TemplateManager:
    return TemplateManager(config.storage_dir / "templates")


class TemplateController(Controller):
    path = "/templates"
    tags = ["Template (模板管理)"]

    dependencies = {"manager": Provide(provide_template_manager, sync_to_thread=False)}

    @get("options", guards=[view_permission])
    async def get_template_options(self, manager: TemplateManager) -> list[str]:
        """获取 category 模板选项列表"""
        files = await manager.list()

        options = [
            f.removesuffix(".category.html")
            for f in files
            # 排除默认模板
            if f.endswith(".category.html") and f != "default.category.html"
        ]

        return ["default", *options]

    @get(guards=[view_permission])
    async def list_templates(self, manager: TemplateManager) -> list[str]:
        """获取模板列表"""
        return await manager.list()

    @get("{file_path:path}", guards=[view_permission])
    async def get_template(
        self,
        manager: TemplateManager,
        file_path: Annotated[str, Parameter(description="模板文件路径")],
    ) -> TemplateContentSchema:
        """获取文件内容"""
        return TemplateContentSchema(content=await manager.read(file_path))

    @put("{file_path:path}", guards=[edit_permission])
    async def save_template(
        self,
        manager: TemplateManager,
        file_path: Annotated[str, Parameter(description="模板文件路径")],
        data: TemplateContentSchema,
    ) -> None:
        """创建或更新模板文件"""
        await manager.write(file_path, data.content)

    @delete("{file_path:path}", guards=[delete_permission])
    async def delete_template(
        self,
        manager: TemplateManager,
        file_path: Annotated[str, Parameter(description="模板文件路径")],
    ) -> None:
        """删除模板文件"""
        await manager.delete(file_path)

    @patch(path="{file_path:path}", guards=[edit_permission])
    async def rename_template(
        self,
        manager: TemplateManager,
        file_path: Annotated[str, Parameter(description="模板文件路径")],
        data: TemplateRenameSchema,
    ) -> None:
        """重命名模板文件"""
        await manager.rename(file_path, data.name)
