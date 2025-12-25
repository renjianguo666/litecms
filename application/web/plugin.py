from __future__ import annotations

import importlib.util as importlib_util
from dataclasses import dataclass, field
from typing import Awaitable, Callable, cast

from litestar import Request, Response

from application.config import config

plugin_dir = config.storage_dir / "plugins"

PluginHandler = Callable[[Request], Awaitable[Response]]


@dataclass
class PluginRegistry:
    cache: dict[str, PluginHandler] = field(default_factory=dict)

    def _load_plugin(self, plugin_name: str) -> None:
        """动态加载插件处理函数"""
        handler_file = plugin_dir / plugin_name / "handlers.py"

        # 检查文件是否存在
        if handler_file.exists():
            module_name = f"plugins.{plugin_name}.handlers"
            spec = importlib_util.spec_from_file_location(module_name, handler_file)

            if spec and spec.loader:
                # 创建并执行模块
                module = importlib_util.module_from_spec(spec)

                try:
                    spec.loader.exec_module(module)
                    handle = getattr(module, "handle", None)
                    if callable(handle):
                        self.cache[plugin_name] = cast(PluginHandler, handle)
                except Exception:
                    ...

    def get_handler(self, plugin_name: str) -> PluginHandler | None:
        """获取插件处理函数（带缓存）"""
        if plugin_name not in self.cache:
            self._load_plugin(plugin_name)
        return self.cache.get(plugin_name)


plugin = PluginRegistry()
