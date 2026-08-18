"""前台插件路由: 动态加载 storages/plugins/{name}/handlers.py 的 handle(request)。

访问 /plugin/{name} 时, 按名查找插件处理器, 有则调用返回 Response,
无则降级 404。加载结果缓存, 不重复 import。

插件目录约定:
    storages/plugins/{name}/handlers.py
        def handle(request) -> Response: ...
"""

from __future__ import annotations

import importlib.util as importlib_util
from dataclasses import dataclass, field
from typing import Callable, cast

from litestar import Request, Response

from application.config import cfg

plugin_dir = cfg.storage_dir / "plugins"

PluginHandler = Callable[[Request], Response]


@dataclass
class PluginRegistry:
    cache: dict[str, PluginHandler] = field(default_factory=dict)

    def _load(self, name: str) -> None:
        handler_file = plugin_dir / name / "handlers.py"
        if not handler_file.exists():
            return
        spec = importlib_util.spec_from_file_location(f"plugins.{name}.handlers", handler_file)
        if not spec or not spec.loader:
            return
        module = importlib_util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            handle = getattr(module, "handle", None)
            if callable(handle):
                self.cache[name] = cast(PluginHandler, handle)
        except Exception:
            # 加载失败静默: 访问该插件时按未找到处理, 走 404
            ...

    def get_handler(self, name: str) -> PluginHandler | None:
        if name not in self.cache:
            self._load(name)
        return self.cache.get(name)


plugin = PluginRegistry()
