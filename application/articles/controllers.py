from __future__ import annotations

from functools import partial
from typing import Annotated
from uuid import UUID

from advanced_alchemy.extensions.litestar.providers import create_service_provider
from advanced_alchemy.filters import SearchFilter
from litestar import Controller, Response, get, post
from litestar.datastructures import FormMultiDict
from litestar.params import FromPath, FromQuery, QueryParameter, URLEncodedBody
from litestar.response import Template
from sqlalchemy.orm import defer, selectinload

from application.accounts.models import User
from application.articles.forms import ArticleDestroyForm, ArticleEditForm, ArticleForm
from application.articles.models import Article
from application.articles.schemas import ArticleLiteSchema
from application.articles.services import ArticleService
from application.config import cfg
from application.guards import PermissionGuard
from application.htmx import HTMXMixin
from application.taxonomies.cache import get_categories_cached
from application.taxonomies.hierarchy import build_tree, resolve_breadcrumbs
from application.taxonomies.schemas import TagSchema
from application.taxonomies.services import (
    CategoryService,
    FeatureService,
    SpecialService,
    TagService,
)
from application.web.cache import invalidate_by_references

view_permission = PermissionGuard("articles:view", "查看文章", "文章管理")
create_permission = PermissionGuard("articles:create", "添加文章", "文章管理")
update_permission = PermissionGuard("articles:update", "更新文章", "文章管理")
destroy_permission = PermissionGuard("articles:destroy", "删除文章", "文章管理")


# 失效前需要读到文章的栏目/标签/专题 (update 失效新挂载页 / destroy 删除前失效), 故带全关系
_ARTICLE_LOADS = [
    selectinload(Article.category),
    selectinload(Article.tags),
    selectinload(Article.specials),
    selectinload(Article.features),
]


class ArticleController(HTMXMixin, Controller):
    path = "/articles"

    dependencies = {
        "service": create_service_provider(ArticleService),
        "category_service": create_service_provider(CategoryService),
        "special_service": create_service_provider(SpecialService),
        "feature_service": create_service_provider(FeatureService),
        "tag_service": create_service_provider(TagService),
    }

    @get(name="articles:index", guards=[view_permission])
    async def index(
        self,
        service: ArticleService,
        search: FromQuery[str | None] = None,
        page: Annotated[int, QueryParameter(ge=1)] = 1,
        page_size: Annotated[int, QueryParameter(ge=1, le=100)] = 10,
    ) -> Template:
        filters = []
        if search:
            filters.append(SearchFilter(field_name="title", value=search, ignore_case=True))
        pagination = await service.paginate(
            *filters,
            page=page,
            page_size=page_size,
            order_by=[("published_at", True)],
            load=[
                selectinload(Article.category),
                selectinload(Article.creator),
                defer(Article.text),
            ],
            schema_type=ArticleLiteSchema,
        )
        # 面包屑: 全量栏目缓存取一次, 模板里 breadcrumbs(row.category_id) 直接解析
        categories = await get_categories_cached(service.repository.session)
        return self.htmx_render(
            template_name="articles.html.j2",
            context={
                "pagination": pagination,
                "breadcrumbs": partial(resolve_breadcrumbs, categories),
            },
        )

    @get("new", name="articles:new", guards=[create_permission])
    async def new(
        self,
        category_service: CategoryService,
        special_service: SpecialService,
        feature_service: FeatureService,
    ) -> Template:
        categories = await get_categories_cached(category_service.repository.session)
        all_features = await feature_service.get_many()
        all_specials = await special_service.get_many()
        form = ArticleForm()
        form.features.choices = [(str(f.id), f.name) for f in all_features]
        form.specials.choices = [(str(s.id), s.name) for s in all_specials]
        form.categories.choices = [(str(c.id), c.name) for c in categories]
        return self.htmx_render(
            template_name="article_form.html.j2",
            context={
                "form": form,
                "category_tree": build_tree(categories),
            },
        )

    @post(name="articles:create", guards=[create_permission])
    async def create(
        self,
        data: URLEncodedBody[FormMultiDict],
        service: ArticleService,
        current_user: User,
        category_service: CategoryService,
        special_service: SpecialService,
        feature_service: FeatureService,
    ) -> Response | Template:
        categories = await get_categories_cached(category_service.repository.session)
        all_features = await feature_service.get_many()
        all_specials = await special_service.get_many()
        form = ArticleForm(data)
        form.features.choices = [(str(f.id), f.name) for f in all_features]
        form.specials.choices = [(str(s.id), s.name) for s in all_specials]
        form.categories.choices = [(str(s.id), s.name) for s in categories]
        if form.validate():
            articles = await service.create_many_for_categories(form.data, creator=current_user)
            # 新增: 只刷新栏目第一页 + 首页 (内置)。新文章详情页还没缓存; 新文章挂的
            # tag/专题页缺失新文章, 脏 300s TTL 自愈 (best-effort)
            for a in articles:
                await invalidate_by_references(a.category)
            return self.htmx_success("添加成功", redirect=data.get("url"))
        return self.htmx_render(
            template_name="article_form.html.j2",
            context={
                "form": form,
                "category_tree": build_tree(categories),
            },
        )

    @get("{item_id:uuid}/edit", name="articles:edit", guards=[update_permission])
    async def edit(
        self,
        item_id: FromPath[UUID],
        service: ArticleService,
        category_service: CategoryService,
        special_service: SpecialService,
        feature_service: FeatureService,
    ) -> Template:
        obj = await service.get(
            item_id,
            load=[
                selectinload(Article.category),
                selectinload(Article.tags),
                selectinload(Article.specials),
                selectinload(Article.features),
            ],
        )
        categories = await get_categories_cached(category_service.repository.session)
        all_features = await feature_service.get_many()
        all_specials = await special_service.get_many()
        form = ArticleEditForm(obj=obj)
        form.features.choices = [(str(f.id), f.name) for f in all_features]
        form.specials.choices = [(str(s.id), s.name) for s in all_specials]
        form.category.choices = [(str(c.id), c.name) for c in categories]
        form.features.data = [str(f.id) for f in obj.features]
        form.specials.data = [str(s.id) for s in obj.specials]

        form.category.data = str(obj.category_id)
        form.tags.data = [t.name for t in obj.tags]
        form.published_at.data = obj.published_at.astimezone(cfg.tzinfo).replace(tzinfo=None, microsecond=0)
        return self.htmx_render(
            template_name="article_form.html.j2",
            context={
                "form": form,
                "category_tree": build_tree(categories),
            },
        )

    @post("{item_id:uuid}", name="articles:update", guards=[update_permission])
    async def update(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: ArticleService,
        category_service: CategoryService,
        special_service: SpecialService,
        feature_service: FeatureService,
    ) -> Response:
        categories = await get_categories_cached(category_service.repository.session)
        all_features = await feature_service.get_many()
        all_specials = await special_service.get_many()
        form = ArticleEditForm(data)
        form.features.choices = [(str(f.id), f.name) for f in all_features]
        form.specials.choices = [(str(s.id), s.name) for s in all_specials]
        form.category.choices = [(str(c.id), c.name) for c in categories]
        if form.validate():
            # update 只失效新值关系: 旧栏目/旧标签 (改挂载场景) 由 TTL 300s 自愈, 不为此增复杂
            updated = await service.update(form.data, item_id, load=_ARTICLE_LOADS, auto_refresh=False)
            # 文章页 + 新挂的栏目/标签/专题页 + 首页 (内置)
            await invalidate_by_references(updated)
            await invalidate_by_references(updated.category)
            for tag in updated.tags:
                await invalidate_by_references(tag)
            for special in updated.specials:
                await invalidate_by_references(special)
            return self.htmx_success("更新成功", redirect=data.get("url"))
        return self.htmx_render(
            template_name="article_form.html.j2",
            context={
                "form": form,
                "category_tree": build_tree(categories),
            },
        )

    @get(
        "{item_id:uuid}/destroy",
        name="articles:destroy_form",
        guards=[destroy_permission],
    )
    async def destroy_form(
        self,
        item_id: FromPath[UUID],
        service: ArticleService,
    ) -> Template:
        article = await service.get(item_id)
        return self.htmx_render(
            template_name="article_destroy.html.j2",
            context={"form": ArticleDestroyForm(obj=article)},
        )

    @post(
        "{item_id:uuid}/destroy",
        name="articles:destroy",
        guards=[destroy_permission],
    )
    async def destroy(
        self,
        item_id: FromPath[UUID],
        data: URLEncodedBody[FormMultiDict],
        service: ArticleService,
    ) -> Response:
        form = ArticleDestroyForm(data)
        obj = await service.get(item_id, load=_ARTICLE_LOADS)
        if form.validate():
            # 删除前挨个失效: delete 后关系会被清空, 只能在删除前取栏目/标签/专题页
            await invalidate_by_references(obj)
            await invalidate_by_references(obj.category)
            for tag in obj.tags:
                await invalidate_by_references(tag)
            for special in obj.specials:
                await invalidate_by_references(special)
            await service.delete(item_id)
            return self.htmx_success("删除成功")
        return self.htmx_render(
            template_name="article_destroy.html.j2",
            context={"form": form},
        )

    # ============ 标签选择 Dialog ============

    @get("tags/dialog", name="articles:tag_dialog", guards=[create_permission])
    async def tag_dialog(
        self,
        tag_service: TagService,
        q: FromQuery[str] = "",
    ) -> Template:
        if q.strip():
            pagination = await tag_service.paginate(
                SearchFilter(field_name="name", value=q, ignore_case=True),
                page=1,
                page_size=20,
                schema_type=TagSchema,
            )
            tags = pagination.items
        else:
            pagination = await tag_service.paginate(
                page=1,
                page_size=10,
                schema_type=TagSchema,
            )
            tags = pagination.items
        return self.htmx_render(
            template_name="tags_dialog.html.j2",
            context={"tags": tags, "q": q},
            block_name=None,
        )
