from __future__ import annotations

from typing import Annotated

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from litestar import Controller, Request, Response, get, params
from litestar.exceptions import ValidationException
from litestar.params import QueryParameter
from litestar.status_codes import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from msgspec import convert
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer, joinedload, selectinload

from application.articles.models import Article
from application.articles.services import ArticleService
from application.contents.enums import PublishStatus
from application.contents.models import Content
from application.mixins import Pagination
from application.pages.services import PageService
from application.seo.hooks import before_request_sitemap_handler
from application.taxonomies.cache import get_categories_cached
from application.taxonomies.hierarchy import resolve_breadcrumbs
from application.taxonomies.models import Category
from application.taxonomies.services import (
    CategoryService,
    SpecialService,
    TagService,
)

from . import urls
from .plugin import plugin
from .schemas import (
    ArticleLiteSchema,
    ArticleSchema,
    CategoryLiteSchema,
    CategorySchema,
    PageSchema,
    SpecialSchema,
    TagSchema,
)
from .template import Template


async def get_breadcrumbs(db_session: AsyncSession, trail: str) -> list[CategoryLiteSchema]:
    """面包屑: 从栏目缓存解析祖先链 (父→子), 转前台轻量 Schema, 零 SQL。"""
    categories = await get_categories_cached(db_session)
    return convert(
        resolve_breadcrumbs(categories, trail=trail),
        list[CategoryLiteSchema],
        from_attributes=True,
    )


class CappedPagination(Pagination):
    """前台分页包装: 仅覆盖 pages 使总页数封顶 max_pages (默认 20)。

    has_next/next_num/iter_pages 均由 pages 派生, 覆盖后自动同步,
    与 QueryParameter(ge=1, le=20) 的参数封顶一致, 不再渲染/导航到 400 页。
    total 保持真实值 ("共 X 条/篇" 不受影响)。
    """

    def __init__(self, pagination: Pagination, max_pages: int = 20):
        super().__init__(
            items=pagination.items,
            total=pagination.total,
            page_size=pagination.page_size,
            page=pagination.page,
        )
        self.max_pages = max_pages

    @property
    def pages(self) -> int:
        return min(super().pages, self.max_pages)


class WebController(Controller):
    path = "/"
    include_in_schema = False
    before_request = before_request_sitemap_handler

    opt = {"exclude_from_auth": True}

    dependencies = {
        "category_service": create_service_provider(CategoryService),
        "page_service": create_service_provider(PageService),
        "article_service": create_service_provider(ArticleService),
        "tag_service": create_service_provider(TagService),
        "special_service": create_service_provider(SpecialService),
    }

    @get("/", name="web:index", cache=True)
    async def index(self) -> Template:
        return Template(template_name=["index.html", "web_index.html"])

    @get(urls.TAG_SHOW, name="web:tag", cache=True)
    async def tag(
        self,
        slug: str,
        tag_service: TagService,
        article_service: ArticleService,
        page: Annotated[int, QueryParameter(ge=1, le=20)] = 1,  # 前台分页页数封顶 1..20
        page_size: params.FromQuery[int] = 20,
    ) -> Template:
        tag = await tag_service.get_one(slug=slug)
        pagination = await article_service.paginate(
            Article.tags.any(id=tag.id),
            Article.status == PublishStatus.PUBLISHED,
            page=page,
            page_size=page_size,
            order_by=[("published_at", True)],
            schema_type=ArticleLiteSchema,
            load=[selectinload(Article.category), selectinload(Article.creator), defer(Article.text)],
        )
        pagination = CappedPagination(pagination)
        return Template(
            ["tags/show.html", "web_tag.html"],
            context={
                "tag": convert(tag, TagSchema, from_attributes=True),
                "pagination": pagination,
            },
        )

    @get(urls.SPECIAL_SHOW, name="web:special", cache=True)
    async def special(
        self,
        slug: str,
        special_service: SpecialService,
        article_service: ArticleService,
        page: Annotated[int, QueryParameter(ge=1, le=20)] = 1,  # 前台分页页数封顶 1..20
        page_size: params.FromQuery[int] = 20,
    ) -> Template:
        special = await special_service.get_one(slug=slug, is_active=True)

        pagination = await article_service.paginate(
            Article.specials.any(id=special.id),
            Article.status == PublishStatus.PUBLISHED,
            page=page,
            page_size=page_size,
            order_by=[("published_at", True)],
            schema_type=ArticleLiteSchema,
            load=[selectinload(Article.category), selectinload(Article.creator), defer(Article.text)],
        )
        pagination = CappedPagination(pagination)

        return Template(
            [f"specials/{special.template}", "web_special.html"],
            context={
                "special": convert(special, SpecialSchema, from_attributes=True),
                "pagination": pagination,
            },
        )

    @get("plugin/{plugin_name:str}", name="web:plugin", cache=True)
    async def plugin_callback(self, request: Request, plugin_name: params.FromPath[str]) -> Response:
        handler = plugin.get_handler(plugin_name)
        if handler is not None:
            return await handler(request)
        return Template(
            "web_404.html",
            status_code=HTTP_404_NOT_FOUND,
        )

    # =========================================================
    # 解析链各视图 (返回 None 表示未命中, 交给下一个)
    # =========================================================
    @get("{path:path}", name="web:resolve", cache=True)
    async def permalink(
        self,
        request: Request,
        db_session: AsyncSession,
        path: params.FromPath[str],
    ) -> Template:
        for view in (self.category_view, self.page_view, self.article_view):
            if response := await view(path, request, db_session):
                return response

        return Template(
            template_name="web_404.html",
            status_code=HTTP_404_NOT_FOUND,
        )

    @get("click", name="web:click")
    async def content_click(
        self,
        db_session: AsyncSession,
        permalink: params.FromQuery[str],
    ) -> str:
        result = await db_session.execute(
            update(Content).where(Content.path == permalink).values(views=Content.views + 1).returning(Content.views)
        )
        views = result.scalar_one_or_none()
        return f"document.write({views or 0});"

    async def category_view(self, path: str, request: Request, db_session: AsyncSession) -> Template | None:
        service = CategoryService(session=db_session)
        category = await service.get_one_or_none(path=path, load=selectinload(Category.children))
        if category is None:
            return None

        breadcrumbs = await get_breadcrumbs(db_session, category.trail)

        article_service = ArticleService(session=db_session)

        filters = [Article.status == PublishStatus.PUBLISHED]

        if category.children:
            query = await db_session.scalars(select(Category.id).where(Category.trail.like(f"{category.trail}.%")))
            filters.append(Article.category_id.in_(query))
        else:
            filters.append(Article.category_id == category.id)

        # 前台分页页数封顶 20: 防深分页 O(N) OFFSET 拖慢事件循环 + 防垃圾 page 值 500
        # 超出 1..20 直接 400, 不做静默截断 (与 tag/special 视图 QueryParameter 校验行为一致)
        try:
            page = int(request.query_params.get("page", 1))
        except (TypeError, ValueError):
            page = 1

        if page < 1 or page > 20:
            # 与 QueryParameter(ge=1, le=20) 校验失败同源: 抛 ValidationException,
            # 走全局 bad_request_handler -> errors/400.html.j2, 无需自定义模板
            raise ValidationException(
                detail="page 参数超出有效范围 1..20",
                status_code=HTTP_400_BAD_REQUEST,
            )

        pagination = await article_service.paginate(
            *filters,
            page=page,
            page_size=category.page_size or 20,
            order_by=[("published_at", True)],
            schema_type=ArticleLiteSchema,
            load=[selectinload(Article.category), selectinload(Article.creator), defer(Article.text)],
        )
        pagination = CappedPagination(pagination)

        template = ["web_category_index.html" if category.children else "web_category.html"]
        if category.template:
            template.insert(
                0,
                f"categories/{category.template}/index.html"
                if category.children
                else f"categories/{category.template}/list.html",
            )

        return Template(
            template,
            context={
                "category": convert(category, CategorySchema, from_attributes=True),
                "breadcrumbs": breadcrumbs,
                "pagination": pagination,
            },
        )

    async def page_view(self, path: str, request: Request, db_session: AsyncSession) -> Template | None:
        page_service = PageService(session=db_session)
        page_obj = await page_service.get_one_or_none(path=path)
        if page_obj is None:
            return None

        template = ["web_page.html"]
        if page_obj.template:
            template.insert(0, f"pages/{page_obj.template}")

        return Template(
            template,
            context={"page": convert(page_obj, PageSchema, from_attributes=True)},
        )

    async def article_view(self, path: str, request: Request, db_session: AsyncSession) -> Template | None:
        article_service = ArticleService(session=db_session)
        article = await article_service.get_one_or_none(
            path=path,
            load=[
                joinedload(Article.category),
                joinedload(Article.creator),
                selectinload(Article.specials),
                selectinload(Article.features),
                selectinload(Article.tags),
            ],
        )
        if article is None:
            return None

        breadcrumbs = await get_breadcrumbs(db_session, article.category.trail)

        template = ["web_article.html"]
        if article.category.template:
            template.insert(0, f"categories/{article.category.template}/article.html")

        return Template(
            template,
            context={
                "article": convert(article, ArticleSchema, from_attributes=True),
                "breadcrumbs": breadcrumbs,
            },
        )
