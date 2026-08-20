from __future__ import annotations

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from litestar import Controller, Request, Response, get, params
from litestar.status_codes import HTTP_404_NOT_FOUND
from msgspec import convert
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer, joinedload, selectinload

from application.articles.models import Article
from application.articles.services import ArticleService
from application.contents.enums import PublishStatus
from application.contents.models import Content
from application.pages.services import PageService
from application.seo.hooks import before_request_sitemap_handler
from application.taxonomies.models import Category
from application.taxonomies.services import (
    CategoryService,
    SpecialService,
    TagService,
)

from . import urls
from .plugin import plugin
from .response import Template
from .schemas import (
    ArticleLiteSchema,
    ArticleSchema,
    CategoryLiteSchema,
    CategorySchema,
    PageSchema,
    SpecialSchema,
    TagSchema,
)


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
        page: params.FromQuery[int] = 1,
        page_size: params.FromQuery[int] = 20,
    ) -> Template:
        tag = await tag_service.get_one(slug=slug)
        pagination = await article_service.paginate(
            Article.tags.any(id=tag.id),
            Article.status == PublishStatus.PUBLISHED,
            page=page,
            page_size=page_size,
            order_by=[("published_at", False)],
            schema_type=ArticleLiteSchema,
            load=[selectinload(Article.category), selectinload(Article.creator), defer(Article.text)],
        )
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
        page: params.FromQuery[int] = 1,
        page_size: params.FromQuery[int] = 20,
    ) -> Template:
        special = await special_service.get_one(slug=slug, is_active=True)

        pagination = await article_service.paginate(
            Article.specials.any(id=special.id),
            Article.status == PublishStatus.PUBLISHED,
            page=page,
            page_size=page_size,
            order_by=[("published_at", False)],
            schema_type=ArticleLiteSchema,
            load=[selectinload(Article.category), selectinload(Article.creator), defer(Article.text)],
        )

        return Template(
            [f"specials/{special.template}", "web_special.html"],
            context={
                "special": convert(special, SpecialSchema, from_attributes=True),
                "pagination": pagination,
            },
        )

    @get("plugin/{plugin_name:str}", name="web:plugin", cache=True)
    async def plugin_callback(self, request: Request, plugin_name: params.FromPath[str]) -> Response | Template:
        handler = plugin.get_handler(plugin_name)
        if handler is not None:
            return handler(request)
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

        breadcrumbs = convert(
            await service.get_many(
                Category.id.in_(category.trail.split(".")),
                order_by=[("trail", False)],
            ),
            list[CategoryLiteSchema],
            from_attributes=True,
        )

        article_service = ArticleService(session=db_session)

        filters = [Article.status == PublishStatus.PUBLISHED]

        if category.children:
            query = await db_session.scalars(select(Category.id).where(Category.trail.like(f"{category.trail}.%")))
            filters.append(Article.category_id.in_(query))
        else:
            filters.append(Article.category_id == category.id)

        pagination = await article_service.paginate(
            *filters,
            page=max(1, int(request.query_params.get("page", 1))),
            page_size=category.page_size or 20,
            order_by=[("published_at", False)],
            schema_type=ArticleLiteSchema,
            load=[selectinload(Article.category), selectinload(Article.creator), defer(Article.text)],
        )

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

        # 面包屑: 取栏目祖先链 (转 CategoryLiteSchema, 统一用 schema)
        ancestor_ids = [part for part in article.category.trail.split(".") if part]
        breadcrumbs = (
            convert(
                await CategoryService(session=db_session).get_many(
                    Category.id.in_(ancestor_ids),
                    order_by=[("trail", False)],
                ),
                list[CategoryLiteSchema],
                from_attributes=True,
            )
            if ancestor_ids
            else []
        )

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
