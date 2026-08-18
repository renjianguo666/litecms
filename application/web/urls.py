"""前台固定功能前缀路由常量。

tag/special 是功能型前缀(非内容 URL), 单独注册精确路由, 优先级高于
catch-all "{path:path}", 不会落进栏目/文章解析链。

前缀写死在此处, 不进 settings.toml: 路由匹配在 app 启动时注册定死,
toml 改了前缀不重启不认, 与写死此处无收益差别。内容/栏目 URL 才需要
运行时即时, 那部分由 catch-all 解析链承担。
"""

from __future__ import annotations

TAG_SHOW = "/t/{slug:str}"
SPECIAL_SHOW = "/s/{slug:str}"


def build_tag_url(slug: str) -> str:
    """生成标签页 URL (供模板/视图拼接, 非 route_reverse)。"""
    return f"/t/{slug}"


def build_special_url(slug: str) -> str:
    """生成专题页 URL。"""
    return f"/s/{slug}"
