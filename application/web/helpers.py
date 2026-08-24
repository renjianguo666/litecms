"""前台模板全局标签 (帝国 CMS 式)。

在 Jinja 模板里直接调用查询数据, 如:
    {% for a in article_select(category=some_id, limit=5, cover=true) %}
    {% for c in category_select() %}

实现: 每个标签用 @pass_context 拿模板上下文 → 取 request → provide_session
复用请求级共享 AsyncSession → 起 Service 查询 → msgspec.convert 转 Schema。
共享数据 (categories) 走文件缓存, 首次查库后续命中内存。
article_select 参数化查询不缓存。
"""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from advanced_alchemy.filters import (
    CollectionFilter,
    ComparisonFilter,
    ExistsFilter,
    LimitOffset,
)
from jinja2 import pass_context
from msgspec import convert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer, joinedload, noload

from application.articles.models import Article
from application.articles.services import ArticleService
from application.contents.enums import PublishStatus
from application.database import sqlalchemy_config
from application.taxonomies.cache import get_categories_cached
from application.taxonomies.hierarchy import build_tree
from application.taxonomies.models import Category, Feature, Special
from application.taxonomies.schemas import CategorySchema
from application.taxonomies.services import (
    SpecialService,
    TagService,
)

from .schemas import (
    ArticleLiteSchema,
    SpecialSchema,
    TagSchema,
)

# from .wechat import WeChatShare


def _coerce_uuid(value: Any) -> UUID:
    """把模板传来的 UUID 或 str (含列表里的元素) 统一成 UUID。

    Jinja 里写字符串 id (如 "019b590f-...") 直接落到 Python 是 str,
    与模型的 UUID 属性直接比较永远不相等, 必须显式转换。
    """
    return value if isinstance(value, UUID) else UUID(str(value))


def _tree_sort_flat(
    categories: list[CategorySchema],
    order_by: str,
    order_dir: Literal["asc", "desc"],
) -> list[CategorySchema]:
    """树感知排序: 父永远在子前, 只对同级兄弟按 order_by 排序, 并列保留 trail 序。

    用 build_tree 把平铺列表还原成树, 每层对兄弟排序后再前序重铺成平铺列表。
    修复全局 sorted 的坑: 子栏目优先级高于父时会跳出父前面破坏树序;
    本函数保证 priority 怎么排都保持在各自的 trail 树内。
    """
    tree = build_tree(categories)

    def _flatten(nodes: list[CategorySchema]) -> list[CategorySchema]:
        ordered = sorted(
            nodes, key=lambda n: getattr(n, order_by), reverse=order_dir == "desc"
        )
        flat: list[CategorySchema] = []
        for node in ordered:
            flat.append(node)
            flat.extend(_flatten(node.children))
        return flat

    return _flatten(tree)


def _session_by_request(request: Any) -> AsyncSession:
    """复用请求级共享 AsyncSession (与控制器 db_session 同一对象)。

    不用 with/不 close: 事务生命周期由 SQLAlchemy 插件的 before_send
    handler 在请求结束时统一 commit/close。模板标签若自行
    with session → close, 会提前关闭共享事务, 下个标签重连触发额外 BEGIN
    (N+1 的根因)。全程共享一个 session = 一个事务 = 一次 BEGIN。
    """
    return sqlalchemy_config.provide_session(request.app.state, request.scope)


# =========================================================
# 栏目 (走文件缓存)
# =========================================================
@pass_context
async def category_select(
    ctx,
    *item: str | UUID,
    parent: str | UUID | None = None,  # 默认 None = 不过滤 = 全部
    under: str | UUID | None = None,
    order_by: str | None = None,
    order_dir: Literal["asc", "desc"] = "asc",
) -> list[CategorySchema]:
    """取栏目 (帝国 CMS 式, 走文件缓存, 内存过滤, 零 SQL)。

    取法互斥, 优先级 under > parent > 位置参数(按 id 取) > 无参(全部), 每次缓存内存过滤, 不查库。
    参数统一传栏目 id (UUID 或 UUID 字符串), 返回 list[CategorySchema] (一维平铺)。

    无任何参数 = 全部栏目 (一维平铺, 树前序: 父在前子在后, 含所有层级):
        {% for c in category_select() %}
          {{ c.name }} ({{ c.trail }})
        {% endfor %}
        {# 只要顶级栏目 (帝国式): 模板里直接过滤 parent_id 为空 #}
        {% for c in category_select() if c.parent_id is none %}

    位置参数 *item: 按 id 取栏目本身, 支持零到多个, 也支持单个 id 列表
    (元素可为 UUID 对象或字符串):
        category_select(id1, id2, id3)            # 取 3 个指定栏目
        category_select("019b590f-2e55-...")      # 字符串 id 也可直接用
        category_select([id1, id2, id3])          # 等价写法
    parent: 取某栏目的直接子栏目 (parent_id == 该 id), 一层; None (默认) = 不过滤;
        顶级栏目在模板里过滤: {% for c in category_select() if c.parent_id is none %}
    under: 取某栏目下面的所有子栏目 (任意层级, 含子/孙/曾孙..., 不含自身),
        trail 前缀匹配, 按树前序平铺, 口径与 category_view 分页一致。
        聚合该栏目下所有文章时:
            {% set cids = category_select(under=category.id)|map(attribute='id')|list %}
            {% for item in article_select(category=cids, limit=4, cover=True) %}
    order_by: 排序字段 (Schema 属性名, 如 "priority" / "id");
        None (默认) = 维持缓存 trail 序 (树前序); under 模式忽略此参数;
        树感知排序: 只对同级兄弟排序, 父永远在子前 (子优先级高于父也不会破坏树序);
    order_dir: 排序方向 (asc 升序, desc 降序; priority 常用 desc, 值大在前)。

    树形导航用嵌套实现层级: 顶级 (模板过滤) 里再 category_select(parent=c.id)
    取直接子级, 逐层往下:
        {% for c in category_select() if c.parent_id is none %}
          {{ c.name }}
          {% for sub in category_select(parent=c.id) %}{% endfor %}
        {% endfor %}
    """
    session = _session_by_request(ctx["request"])
    cats = await get_categories_cached(session)

    if under is not None:
        node = next((c for c in cats if c.id == _coerce_uuid(under)), None)
        if node is None:
            return []
        return [c for c in cats if c.trail.startswith(f"{node.trail}.")]

    if parent is not None:
        parent_uuid = _coerce_uuid(parent)
        result = [c for c in cats if c.parent_id == parent_uuid]  # 直接子级
    elif item:
        wanted: set[UUID] = set()
        for x in item:
            if isinstance(x, (list, tuple)):
                wanted.update(_coerce_uuid(v) for v in x)
            else:
                wanted.add(_coerce_uuid(x))
        result = [c for c in cats if c.id in wanted]
    else:
        result = list(cats)  # 全部栏目 (一维平铺, 树前序, 含所有层级)

    if order_by is not None:
        # 树感知排序: 只对同级兄弟按 order_by 排, 父永远在子前。
        # 修复全局 sorted 的坑: 子优先级高于父也不会跳出父前面。
        result = _tree_sort_flat(result, order_by, order_dir)

    return result


# =========================================================
# 专题 / 标签 (参数化查询, 对齐 article_select 模式, 不缓存)
# =========================================================
@pass_context
async def tag_select(
    ctx,
    limit: int | None = None,
    order_by: str = "created_at",
    order_dir: Literal["asc", "desc"] = "desc",
) -> list[TagSchema]:
    """查询标签列表 (参数化)。

    limit: 取条数, None=全部;
    order_by: 排序字段 (created_at / name);
    order_dir: 排序方向 (desc=新建在前, asc=旧在前)。
    """
    session = _session_by_request(ctx["request"])
    filters: list[Any] = []
    if limit:
        filters.append(LimitOffset(limit=limit, offset=0))
    result = await TagService(session=session).get_many(
        *filters,
        order_by=[(order_by, order_dir == "desc")],
    )
    return convert(result, list[TagSchema], from_attributes=True)


@pass_context
async def special_select(
    ctx,
    limit: int | None = None,
    order_by: str = "priority",
    order_dir: Literal["asc", "desc"] = "desc",
    active_only: bool = True,
) -> list[SpecialSchema]:
    """查询专题列表 (参数化)。

    active_only: true 只取启用的 (is_active=True);
    limit: 取条数, None=全部;
    order_by: 排序字段 (priority / created_at);
    order_dir: 排序方向 (desc=优先级高在前)。
    """
    session = _session_by_request(ctx["request"])
    filters: list[Any] = []
    if active_only:
        filters.append(Special.is_active.is_(True))
    if limit:
        filters.append(LimitOffset(limit=limit, offset=0))
    result = await SpecialService(session=session).get_many(
        *filters,
        order_by=[(order_by, order_dir == "desc")],
    )
    return convert(result, list[SpecialSchema], from_attributes=True)


# =========================================================
# 文章查询 (核心标签, 参数丰富)
# =========================================================
@pass_context
async def article_select(
    ctx,
    category: str | UUID | list[str | UUID] | None = None,
    special: str | list[str] | None = None,
    feature: str | list[str] | None = None,
    limit: int = 10,
    cover: bool = False,
    order_by: str = "published_at",
    order_dir: Literal["desc", "asc"] = "desc",
) -> list[ArticleLiteSchema]:
    """查询已发布文章列表。

    category: 按 id (UUID) 过滤, 支持单个或列表;
    special/feature: 按 slug (英文标识) 过滤, 支持单个或列表;
    limit: 取条数;
    cover: true 时只取有封面的;
    order_by/order_dir: 排序字段与方向。
    """
    session = _session_by_request(ctx["request"])
    filters: list[Any] = [
        ComparisonFilter(field_name="status", operator="eq", value=PublishStatus.PUBLISHED),
    ]
    if cover:
        filters.append(Article.cover_url.isnot(None))
        filters.append(Article.cover_url != "")

    if category is not None:
        if isinstance(category, list):
            filters.append(CollectionFilter(field_name="category_id", values=category))
        else:
            filters.append(ComparisonFilter(field_name="category_id", operator="eq", value=category))

    if special is not None:
        if isinstance(special, list):
            filters.append(ExistsFilter([Article.specials.any(Special.slug.in_(special))]))
        else:
            filters.append(Article.specials.any(Special.slug == special))

    if feature is not None:
        if isinstance(feature, list):
            filters.append(ExistsFilter([Article.features.any(Feature.slug.in_(feature))]))
        else:
            filters.append(Article.features.any(Feature.slug == feature))

    sort_order = order_dir == "desc"
    load = [
        defer(Article.text),
        joinedload(Article.creator),
        joinedload(Article.category).options(noload(Category.parent), noload(Category.children)),
    ]

    service = ArticleService(session=session)
    result = await service.get_many(
        *filters,
        LimitOffset(limit=limit, offset=0),
        order_by=[(order_by, sort_order)],
        load=load,
    )

    return convert(result, list[ArticleLiteSchema], from_attributes=True)


# =========================================================
# 微信分享   参见  ./wechat.py
# =========================================================
# @pass_context
# async def wechat_share(
#     ctx,
#     title: str = "",
#     desc: str = "",
#     link: str = "",
#     img: str = "",
#     *api_list: str,
# ) -> str:
#     """渲染微信 JS-SDK 分享 JS, 供模板 | safe 直出。

#     凭据 (wechat_app_id / wechat_app_secret) 从 .env 读 (cfg), 属部署级配置;
#     未配置时返回空串, 不注入 JS。签名 URL 用当前 request.url。

#     access_token / jsapi_ticket 进程级缓存, 用 aiohttp 异步获取,
#     不阻塞事件循环。
#     """
#     share = WeChatShare(ctx["request"], *api_list)
#     return await share(title=title, desc=desc, link=link, img=img)
