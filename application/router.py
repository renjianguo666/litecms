from __future__ import annotations

from litestar import Router
from litestar.static_files import create_static_files_router

from application.accounts.controllers.auth import AuthController
from application.accounts.controllers.profile import ProfileController
from application.accounts.controllers.role import RoleController
from application.accounts.controllers.user import UserController
from application.articles.controllers import ArticleController
from application.config import cfg
from application.dashboard.controllers import DashboardController
from application.media.controllers import MediaController
from application.pages.controllers import PageController
from application.seo.controllers import SEOController
from application.settings.controllers import SettingController
from application.taxonomies.controllers import (
    CategoryController,
    FeatureController,
    SpecialController,
    TagController,
)
from application.themes.controllers import TemplateController
from application.web.controllers import WebController

route_handlers = [
    Router(
        path=cfg.admin_url_prefix,
        include_in_schema=False,
        route_handlers=[
            AuthController,
            DashboardController,
            ProfileController,
            UserController,
            RoleController,
            CategoryController,
            FeatureController,
            TagController,
            SpecialController,
            ArticleController,
            PageController,
            SEOController,
            TemplateController,
            MediaController,
            SettingController,
        ],
    ),
    WebController,
    create_static_files_router(
        path="/static",
        directories=[cfg.public_dir / "static"],
        opt={
            "exclude_from_auth": True,
        },
    ),
    create_static_files_router(
        path="/uploads",
        directories=[cfg.public_dir / "uploads"],
        opt={
            "exclude_from_auth": True,
        },
    ),
]
