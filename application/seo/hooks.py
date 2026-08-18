from __future__ import annotations

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from advanced_alchemy.filters import LimitOffset
from litestar import Request
from litestar.exceptions import NotFoundException
from litestar.response import Template
from msgspec import convert
from sqlalchemy.orm import load_only, selectinload

from application.contents.enums import PublishStatus
from application.contents.models import Content
from application.contents.services import ContentService
from application.deps import provide_services
from application.seo.schemas import SitemapSchema
from application.settings.manager import get_settings
from application.taxonomies.models.categories import Category
from application.taxonomies.services import CategoryService

SITEMAP_SUFFIX = "/sitemap.xml"


async def before_request_sitemap_handler(request: Request) -> Template | None:

    path = request.url.path

    if not path.endswith(SITEMAP_SUFFIX):
        return

    # sitemap 开关关闭则 404, 不生成(设置页"启用 Sitemap"控制)
    if not get_settings("sitemap_enabled", True):
        raise NotFoundException("Sitemap 已禁用")

    category_path = path[: -len(SITEMAP_SUFFIX)]

    async with provide_services(
        create_service_provider(CategoryService),
        create_service_provider(ContentService),
    ) as (category_service, content_service):
        if category_path:
            category = await category_service.get_one(Category.path == category_path)
            categories = await category_service.get_many(
                Category.domain == category.domain
            )

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

    return Template(
        template_name="sitemap.xml.j2",
        context={"entries": entries},
        media_type="application/xml",
    )
