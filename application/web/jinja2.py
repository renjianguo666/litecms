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
from .wechat import WeChatShare


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
    id: UUID | list[UUID] | None = None,
    parent_id: UUID | None = None,
    order_by: str | None = None,
    order_dir: Literal["asc", "desc"] = "asc",
) -> list[CategorySchema]:
    """取栏目一层 (帝国 CMS 式, 走文件缓存, 内存过滤, 零 SQL)。

    标签只返回一维列表 (一层); 要多层在模板里嵌套循环, 用上一层的 id
    作 parent_id 再调一次。每次都是缓存内存过滤, 不查库, 无 N+1。

    id: 按 id 取栏目本身 (单个或列表); 传 id 时忽略 parent_id;
    parent_id: 取该栏目的直接子栏目; None (默认) = 顶级栏目;
    order_by: 排序字段 (Schema 属性名, 如 "priority" / "id");
        None (默认) = 维持缓存 trail 序 (树前序);
    order_dir: 排序方向 (asc 升序, desc 降序; priority 常用 desc, 值大在前)。

    多层示例 (模板嵌套, 想几层套几层):
        {% for c in category_select(order_by="priority", order_dir="desc") %}
          {{ c.name }}
          {% for sub in category_select(parent_id=c.id, order_by="priority", order_dir="desc") %}
            {% for sub2 in category_select(parent_id=sub.id) %}{% endfor %}
          {% endfor %}
        {% endfor %}
    """
    session = _session_by_request(ctx["request"])
    cats = await get_categories_cached(session)

    if id is not None:
        if isinstance(id, UUID):
            result = [c for c in cats if c.id == id]
        else:
            id_set = set(id)
            result = [c for c in cats if c.id in id_set]
    else:
        result = [c for c in cats if c.parent_id == parent_id]

    if order_by is not None:
        result = sorted(
            result, key=lambda c: getattr(c, order_by), reverse=order_dir == "desc"
        )

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
        order_by=[(order_by, order_dir == "asc")],
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
        order_by=[(order_by, order_dir == "asc")],
    )
    return convert(result, list[SpecialSchema], from_attributes=True)


# =========================================================
# 文章查询 (核心标签, 参数丰富)
# =========================================================
@pass_context
async def article_select(
    ctx,
    category: UUID | list[UUID] | None = None,
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
        ComparisonFilter(
            field_name="status", operator="eq", value=PublishStatus.PUBLISHED
        ),
    ]
    if cover:
        filters.append(Article.cover_url.isnot(None))
        filters.append(Article.cover_url != "")

    if category is not None:
        if isinstance(category, list):
            filters.append(CollectionFilter(field_name="category_id", values=category))
        else:
            filters.append(
                ComparisonFilter(
                    field_name="category_id", operator="eq", value=category
                )
            )

    if special is not None:
        if isinstance(special, list):
            filters.append(
                ExistsFilter([Article.specials.any(Special.slug.in_(special))])
            )
        else:
            filters.append(Article.specials.any(Special.slug == special))

    if feature is not None:
        if isinstance(feature, list):
            filters.append(
                ExistsFilter([Article.features.any(Feature.slug.in_(feature))])
            )
        else:
            filters.append(Article.features.any(Feature.slug == feature))

    sort_order = order_dir == "asc"
    load = [
        defer(Article.text),
        joinedload(Article.creator),
        joinedload(Article.category).options(
            noload(Category.parent), noload(Category.children)
        ),
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
# 微信分享
# =========================================================
@pass_context
async def wechat_share(
    ctx,
    title: str = "",
    desc: str = "",
    link: str = "",
    img: str = "",
    *api_list: str,
) -> str:
    """渲染微信 JS-SDK 分享 JS, 供模板 | safe 直出。

    凭据 (wechat_app_id / wechat_app_secret) 从 settings.toml 读;
    未配置时返回空串, 不注入 JS。签名 URL 用当前 request.url。

    access_token / jsapi_ticket 进程级缓存, 用 aiohttp 异步获取,
    不阻塞事件循环。
    """
    share = WeChatShare(ctx["request"], *api_list)
    return await share(title=title, desc=desc, link=link, img=img)
