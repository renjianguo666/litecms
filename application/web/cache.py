"""前台响应缓存失效 (路径计算式, 最少原则)。

前台页面缓存 key = ``method + path + query`` (Litestar default_cache_key_builder,
见 response_cache 中间件)。本模块不建索引、不需前台登记: 后台写操作后, 把受影响
的对象传给 ``invalidate_by_references``, 它取对象对应前台页面的路径 (无 query 的
第一页), 直接算出 key 删文件。路径 → key 是确定性映射, 所以不需要"登记哪些 key
用了这个引用"。

列表页只处理第一页: 列表按时间倒序, 变更内容都在第一页 (帝国CMS 生成静态页也是
只刷第一页/当前页), 分页 2+ 内容不变, 不碰。

缓存是 best-effort (TTL 300s 兜底), 失效推导同样 best-effort: 未显式传的关系页
(如文章挂的标签/专题页, 以及所有分页 2+) 脏了由 TTL 自愈, 绝不让失效拖垮主流程。

调用方式显式直白: ``invalidate_by_references`` 只收单个领域对象 (鸭子类型取
``entity.path``, 不 import 任何模型), 首页 "/" 内置默认失效。CUD 后把受影响对象
挨个传进来即可 (删几个调几次), 无任何隐式魔法。update 只失效新值关系, 旧挂载页
(如改栏目前的旧栏目) 由 TTL 自愈。

对象路径统一鸭子类型取 ``entity.path``: Article/Category/Page 的 path 是数据库真实
路径; Tag/Special 的 path property 已补上前缀 (build_tag_url/build_special_url)。

索引已废弃 (v2 起): 见 git 历史 register_cache_references / entity_references / cacherefs/。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, cast

from litestar.stores.file import FileStore

from application.config import cfg

logger = logging.getLogger(__name__)


def cache_key_path(entity: Any) -> str | None:
    """对象对应前台页面的路径 (第一页, 无 query), 即缓存 key 的路径部分。

    纯鸭子类型: 只认 ``entity.path``, 不依赖任何模型类。Tag/Special 的 path property
    返回补上前缀的页面路径; Article/Category/Page 的 path 是数据库真实路径 (注意
    不能用 url: url 在 category.domain 非空时会剥离域名目录前缀, 而本应用实际能缓存
    (200) 的请求路径是带前缀的 DB path)。

    静默: 取不到 path 返回 None (调用方跳过), 绝不抛异常——缓存是 best-effort,
    失效推导失败不影响主流程 (脏页由 TTL 300s 自愈)。Feature 无独立前台页面
    (无 path), 返回 None。
    """
    return getattr(entity, "path", None)


def _cache_key(path: str) -> str:
    """页面路径 → 缓存 key (与 Litestar default_cache_key_builder 无 query 时一致)。"""
    return f"GET{path}"


def runtime_response_store() -> FileStore:
    """运行时响应缓存 store (runtime 目录下的 response 命名空间, 见 config.stores)。"""

    return cast(FileStore, cfg.stores.get("response"))


async def invalidate_by_references(entity: Any) -> int:
    """后台增删改后调用: 使对象相关前台页面缓存失效, 返回删除的 key 数。

    单参数, 只收领域对象 (鸭子类型取 ``entity.path``)。删两个 key: 首页 "GET/"
    (内置默认——任何对象变化都可能影响首页, 不显式传) + 对象页面 "GET{path}"
    (对象无 path 时只删首页)。CUD 后把受影响对象挨个传进来即可, 删几个调几次。

    只处理对象对应页面的第一页 (无 query); 分页 2+ 与未显式传的关系页由 TTL 自愈。
    key 不存在时 delete 是 no-op。

    静默: 对象无 path / 取 store 失败 / delete 失败都只记日志后继续, 绝不抛异常——
    缓存失效是 best-effort, 任何异常都不能影响后台写操作主流程 (脏页由 TTL 自愈)。
    """
    # 首页默认失效: 任何对象变化都可能影响首页 (推荐位/最新文章/导航等)
    keys = {"GET/"}
    if path := cache_key_path(entity):
        keys.add(_cache_key(path))
    # runtime_response_store 由 cfg.stores 缓存初始化, get 保证返回 Store, 不会抛
    store = runtime_response_store()
    deleted = 0
    for key in keys:
        try:
            await store.delete(key)  # key 不存在时 delete 是 no-op
            deleted += 1
        except Exception:  # noqa: BLE001 - 静默, 不影响主流程
            logger.exception("响应缓存失效: delete %s 失败", key)
    return deleted


async def purge_all_cache() -> None:
    """全量清空响应缓存 (设置/模板/批量操作等无法精确到引用时用)。"""
    await runtime_response_store().delete_all()


# =========================================================================
# 周期性过期清理任务 (防止 response 目录无限累积)
# =========================================================================


async def _cleanup_loop(interval: int) -> None:
    while True:
        await asyncio.sleep(interval)
        try:
            await runtime_response_store().delete_expired()
        except Exception:  # noqa: BLE001 - 清理失败不影响主流程
            logger.exception("response cache delete_expired 失败")


def start_cleanup_task(interval: int = 60) -> asyncio.Task:
    """启动后台清理任务, 返回 task (注册进 on_shutdown 时 cancel 即可)。"""
    return asyncio.create_task(_cleanup_loop(interval))


def stop_cleanup_task(task: asyncio.Task | None) -> None:
    if task is not None:
        task.cancel()
