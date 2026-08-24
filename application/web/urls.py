"""前台固定功能前缀路由常量。

tag/special 是功能型前缀(非内容 URL), 单独注册精确路由, 优先级高于
catch-all "{path:path}", 不会落进栏目/文章解析链。

前缀来自 cfg.tag_url_prefix / cfg.special_url_prefix 配置项, 统一经
normalize_path 规范为 单个 / 开头、不以 / 结尾。路由匹配在 app 启动时
注册定死, 改前缀需重启生效。内容/栏目 URL 由 catch-all 解析链承担。
"""

from __future__ import annotations

from litestar.utils.path import normalize_path

from application.config import cfg


def _normalize_prefix(prefix: str) -> str:
    """URL 前缀规范化: 空值直接报错(避免 /{slug} 盖住 catch-all), 其余交给 normalize_path。"""
    if not prefix.strip():
        raise ValueError("tag/special url_prefix 不能为空")
    return normalize_path(prefix)


TAG_SHOW = f"{_normalize_prefix(cfg.tag_url_prefix)}/{{slug:str}}"
SPECIAL_SHOW = f"{_normalize_prefix(cfg.special_url_prefix)}/{{slug:str}}"


def build_tag_url(slug: str) -> str:
    """生成标签页 URL (供模板/视图拼接, 非 route_reverse)。"""
    return f"{_normalize_prefix(cfg.tag_url_prefix)}/{slug}"


def build_special_url(slug: str) -> str:
    """生成专题页 URL。"""
    return f"{_normalize_prefix(cfg.special_url_prefix)}/{slug}"
