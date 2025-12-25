from litestar import Router
from litestar.static_files import create_static_files_router

from application.accounts.controllers import (
    AccessController,
    PermissionController,
    RoleController,
    UserController,
)
from application.articles.controllers import ArticleController
from application.config import config
from application.media import UploadController
from application.taxonomies.controllers import (
    CategoryController,
    FeatureContentController,
    FeatureController,
    SpecialContentController,
    SpecialController,
    TagContentController,
    TagController,
)
from application.themes import TemplateController
from application.web.controllers import WebController

route_handlers = [
    Router(
        path=config.api_prefix,
        route_handlers=[
            AccessController,
            PermissionController,
            RoleController,
            UserController,
            CategoryController,
            FeatureController,
            TagController,
            TagContentController,
            SpecialController,
            SpecialContentController,
            FeatureContentController,
            ArticleController,
            UploadController,
            TemplateController,
        ],
    ),
    WebController,
    create_static_files_router(
        path=config.assets_url, directories=[config.assets_dir], name="assets"
    ),
    create_static_files_router(path="/", directories=[config.public_dir]),
]
