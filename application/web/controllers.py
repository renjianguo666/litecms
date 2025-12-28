from __future__ import annotations

import json

from litestar import Controller, Request, Response, get
from litestar.status_codes import HTTP_404_NOT_FOUND
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from application.articles.models import Article
from application.articles.services import ArticleRepository
from application.config import config
from application.contents.models import Content
from application.contents.schemas import ContentLiteSchema
from application.contents.services import ContentRepository
from application.taxonomies.models import Category
from application.taxonomies.services import (
    CategoryRepository,
    SpecialRepository,
    TagRepository,
)

from . import exceptions, schemas, urls, utils
from .middleware import PathNormalizationMiddleware
from .plugin import plugin


class WebController(Controller):
    path = "/"
    exception_handlers = exceptions.exception_handler
    include_in_schema = False
    opt = {"exclude_from_auth": True}
    middleware = [PathNormalizationMiddleware()]

    @get("/", cache=300)
    async def index(self, request: Request) -> Response:
        return await utils.render_template(
            request=request,
            template_name=["index.html", "_index.html"],
        )

    @get("{path:path}")
    async def permalink(
        self,
        request: Request,
        db_session: AsyncSession,
        path: str,
    ) -> Response:
        for view in [self.category_view, self.article_view]:
            if response := await view(path, request, db_session):
                return response

        return await utils.render_template(
            request, template_name="_404.html", status_code=HTTP_404_NOT_FOUND
        )

    @get(urls.SPECIAL_SHOW)
    async def specials(
        self, request: Request, db_session: AsyncSession, slug: str
    ) -> Response:
        repo = SpecialRepository(session=db_session)
        special = await repo.get(item_id=slug, id_attribute="slug")
        pagination = await utils.paginate(
            request,
            ContentLiteSchema,
            ContentRepository(session=db_session),
            Content.specials.any(id=special.id),
            order_by=Content.created_at.desc(),
            page_size=10,
        )
        return await utils.render_template(
            request,
            template_name=[f"special_{special.slug}.html", "_special.html"],
            special=special,
            items=pagination.items,
            pagination=pagination,
        )

    @get(urls.TAG_SHOW)
    async def tag(
        self, request: Request, db_session: AsyncSession, slug: str | None = None
    ) -> Response:
        repo = TagRepository(session=db_session)
        tag = await repo.get(item_id=slug, id_attribute="slug")
        pagination = await utils.paginate(
            request,
            ContentLiteSchema,
            ContentRepository(session=db_session),
            Content.tags.any(id=tag.id),
            order_by=Content.created_at.desc(),
            page_size=10,
        )
        return await utils.render_template(
            request,
            template_name=[f"tag_{tag.slug}.html", "_tag.html"],
            tag=tag,
            items=pagination.items,
            pagination=pagination,
        )

    @get("plugin/{plugin_name:str}")
    async def plugin_callback(self, request: Request, plugin_name: str) -> Response:
        try:
            handler = plugin.get_handler(plugin_name)
            if handler:
                return await handler(request)
        except Exception:
            pass

        return await utils.render_template(
            request, template_name="_404.html", status_code=HTTP_404_NOT_FOUND
        )

    async def category_view(
        self,
        path: str,
        request: Request,
        session: AsyncSession,
    ) -> Response | None:
        repo = CategoryRepository(session=session)
        category = await repo.get_one_or_none(path=path)

        if category is None:
            return

        category_schema = schemas.Category.model_validate(category).model_dump()

        breadcrumb_schema = schemas.breadcrumb_list_adapter.dump_python(
            schemas.breadcrumb_list_adapter.validate_python(
                await repo.list(
                    Category.id.in_(category.trail.split(".")),
                    order_by=Category.trail.asc(),
                )
            )
        )

        pagination = await utils.paginate(
            request,
            ContentLiteSchema,
            ContentRepository(session=session),
            category_id=category.id,
            order_by=Content.created_at.desc(),
            page_size=category.page_size,
        )

        return await utils.render_template(
            request,
            template_name=f"{category.template or ''}_category.html",
            category=category_schema,
            breadcrumbs=breadcrumb_schema,
            pagination=pagination,
            items=pagination.items,
        )

    async def article_view(
        self, path: str, request: Request, session: AsyncSession
    ) -> Response | None:
        repo = ArticleRepository(session=session)
        article = await repo.get_one_or_none(
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
            return

        data = schemas.Article.model_validate(article)

        category_repo = CategoryRepository(session=session)

        breadcrumbs = schemas.breadcrumb_list_adapter.validate_python(
            await category_repo.list(
                Category.id.in_(article.category.trail.split(".")),
                order_by=Category.trail.asc(),
            )
        )

        return await utils.render_template(
            request,
            template_name=[
                f"{article.category.template or ''}_article.html",
                "_article.html",
            ],
            article=data,
            breadcrumbs=breadcrumbs,
        )

    @get(path=[config.admin_url, f"{config.admin_url}/{{path:path}}"])
    async def admin_enter(self, request: Request, path: str | None = None) -> Response:
        entry = "resources/main.tsx"
        if config.debug:
            assets_js = '<script type="module" src="http://localhost:5173/@vite/client"></script>'
            assets_js += '<script type="module" src="http://localhost:5173/resources/main.tsx"></script>'
            assets_css = ""
        else:
            manifest_path = config.assets_dir / ".vite/manifest.json"
            assets = json.loads(manifest_path.read_bytes())
            entry_data = assets[entry]  # 简化变量名

            # 1. 注入 CSS (您已成功实现)
            assets_css = "\n".join(
                f'<link rel="stylesheet" href="{request.app.route_reverse("assets", file_path=css)}">'
                for css in entry_data.get("css", [])
            )

            # 2. 准备所有 JS 资源列表（包括主文件和它的所有 vendor 依赖）
            all_js_files = []

            # 首先，添加所有依赖的 JS 块 (Imports)，这包括 vendor-ui, vendor-form 等
            # 注意：这里需要从 manifest 中查找依赖块的 'file' 路径
            for import_key in entry_data.get("imports", []):
                # import_key 是 "_vendor-ui-1PRpn-I_.js"
                imported_file_data = assets.get(import_key)
                if imported_file_data:
                    all_js_files.append(
                        imported_file_data["file"]
                    )  # 得到 "assets/vendor-ui-1PRpn-I_.js"

            # 最后，添加主入口文件
            all_js_files.append(entry_data["file"])  # 得到 "assets/main-DkjrRI4g.js"

            # 3. 注入所有 JS 文件
            assets_js = "\n".join(
                f'<script type="module" src="{request.app.route_reverse("assets", file_path=js_file)}"></script>'
                for js_file in all_js_files
            )
        html = ADMIN_TEMPLATE.format(
            admin_url=config.admin_url,
            admin_title=config.admin_title,
            assets_js=assets_js,
            assets_css=assets_css,
        )
        return Response(content=html, media_type="text/html")


ADMIN_TEMPLATE = """<!doctype html>
<html>
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="app-basepath" content="{admin_url}" />
  <title>{admin_title}</title>
  {assets_css}
</head>
<body>
  <div id="root"></div>
  {assets_js}
</body>
</html>"""
