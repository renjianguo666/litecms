"""前台 sitemap.xml 生成。

sitemap 是全站单请求分配最大的路径: 一次拉 50k 行 + 渲染整份 XML。
它由 WebController.before_request 短路返回, 但**命中 web 路由的响应缓存**:

  - 读路径 (routes/http.py _get_response_for_request): 缓存命中在
    before_request 之前短路 → 命中时 hook 不执行, 50k 行重建零发生;
  - 写路径 (ResponseCacheMiddleware): before_request 返回的 Response
    同样流经 wrapped_send 被捕获 → 写入 response store (TTL 300s)。

所以这里**不需要手动 FileStore**: 响应缓存已把"每次请求全量重建"降为
"每 300s 最多重建一次", 与全站其它前台页保持一致。本模块只负责 miss 时
构建 XML, 复用请求级共享 AsyncSession (_session_by_request), 不新开事务。
"""

from __future__ import annotations

from advanced_alchemy.filters import LimitOffset
from litestar import Request
from litestar.exceptions import NotFoundException
from litestar.response import Response
from msgspec import convert
from sqlalchemy.orm import load_only, selectinload

from application.contents.enums import PublishStatus
from application.contents.models import Content
from application.contents.services import ContentService
from application.seo.schemas import SitemapSchema
from application.settings.manager import get_settings
from application.taxonomies.models.categories import Category
from application.taxonomies.services import CategoryService
from application.web.helpers import _session_by_request
from application.web.template import template_engine

SITEMAP_SUFFIX = "/sitemap.xml"


async def _build_sitemap(request: Request) -> str:
    """查库 + 渲染 XML (仅响应缓存 miss 时执行)。"""

    session = _session_by_request(request)

    category_service = CategoryService(session=session)
    content_service = ContentService(session=session)

    category_path = request.url.path[: -len(SITEMAP_SUFFIX)]

    if category_path:
        category = await category_service.get_one(Category.path == category_path)
        categories = await category_service.get_many(Category.domain == category.domain)
    else:
        categories = await category_service.get_many(Category.domain.is_(None))

    results = await content_service.get_many(
        Content.category_id.in_([c.id for c in categories]),
        Content.status == PublishStatus.PUBLISHED,
        LimitOffset(limit=50000, offset=0),
        load=[
            selectinload(Content.category).load_only(Category.domain),
            load_only(Content.path, Content.updated_at, Content.category_id),
        ],
        order_by=[("published_at", True)],
    )
    entries = convert(results, list[SitemapSchema], from_attributes=True)

    template = template_engine.get_template("sitemap.xml.j2")
    return await template.render_async(entries=entries)


async def before_request_sitemap_handler(request: Request) -> Response | None:
    # 先短路非 sitemap 请求: 避免 sitemap 开关关闭时误伤整个前台
    if not request.url.path.endswith(SITEMAP_SUFFIX):
        return

    # sitemap 开关关闭则 404, 不生成(设置页"启用 Sitemap"控制)
    if not get_settings("sitemap_enabled", True):
        raise NotFoundException("Sitemap 已禁用")

    xml = await _build_sitemap(request)
    return Response(xml.encode("utf-8"), media_type="application/xml")
