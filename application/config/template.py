"""Jinja2 异步模板引擎配置

通过直接使用 Jinja2 的 render_async 方法，支持在模板中调用异步函数查询数据库。
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar

from jinja2 import Environment, FileSystemLoader, pass_context
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template.config import TemplateConfig

if TYPE_CHECKING:
    from .settings import Settings

F = TypeVar("F", bound=Callable[..., Any])

# 模板全局函数注册表
TEMPLATE_GLOBALS: dict[str, Callable[..., Any]] = {}


def global_function(
    name: str | None = None,
    *,
    use_context: bool = False,
) -> Callable[[F], F]:
    """装饰器：将函数注册为 Jinja2 模板全局函数"""

    def decorator(func: F) -> F:
        key = name if name is not None else func.__name__
        if use_context:
            TEMPLATE_GLOBALS[key] = pass_context(func)
        else:
            TEMPLATE_GLOBALS[key] = func
        return func

    return decorator


def _auto_discover_template_modules() -> None:
    """自动扫描并导入 application 下所有子应用的 jinja2.py"""
    import application

    package_path = application.__path__
    package_name = application.__name__

    for module_info in pkgutil.iter_modules(package_path):
        if module_info.ispkg:
            # 尝试导入子包下的 jinja2 模块
            templates_module_name = f"{package_name}.{module_info.name}.jinja2"
            try:
                importlib.import_module(templates_module_name)
            except ModuleNotFoundError:
                # 子包下没有 jinaj2.py，跳过
                pass


def create_template_config(settings: Settings) -> TemplateConfig:
    """创建模板引擎配置"""
    # 自动发现并导入所有 templates.py 模块
    _auto_discover_template_modules()

    env = Environment(
        loader=FileSystemLoader(
            [
                settings.app_dir / "web" / "templates",
                settings.storage_dir / "templates",
            ]
        ),
        enable_async=True,
    )

    # 直接在 Jinja2 globals 中注册异步函数
    env.globals.update(TEMPLATE_GLOBALS)

    return TemplateConfig(
        engine=JinjaTemplateEngine.from_environment(env),
    )
