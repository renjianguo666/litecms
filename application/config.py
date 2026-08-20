from __future__ import annotations

import os
from functools import cached_property, lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from litestar.config.compression import CompressionConfig
from litestar.config.csrf import CSRFConfig
from litestar.config.response_cache import ResponseCacheConfig, default_do_cache_predicate
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.openapi import OpenAPIConfig
from litestar.stores.file import FileStore
from litestar.stores.registry import StoreRegistry
from litestar.template.config import TemplateConfig
from msgspec import Struct, convert

# 1. 加载 .env 文件
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config(Struct, rename="upper", dict=True):
    """
    应用配置
    """

    # === 安全 ===
    secret_key: str = "change-me"

    # === 应用基础 ===
    debug: bool = False

    root_dir: Path = BASE_DIR
    app_dir: Path = BASE_DIR / "application"
    storage_dir: Path = BASE_DIR / "storages"
    public_dir: Path = BASE_DIR / "public"

    # === 请求体大小限制（Litestar 框架层拦截，所有 POST/PUT/PATCH 统一生效） ===
    request_max_body_size: int = 10 * 1024 * 1024  # 10MB

    # === 媒体存储 ===
    oss_access_key: str = ""
    oss_secret_key: str = ""
    oss_region: str = ""
    oss_bucket: str = ""
    oss_prefix: str = "uploads"
    oss_use_internal: bool = False
    oss_cdn_url: str = ""

    # === 数据库 ===
    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR}/storages/cms.db"
    database_echo: bool = False

    # === 时区 ===
    # 前端表单提交的 naive datetime 按此时区解释（用户本地时区）
    timezone: str = "Asia/Shanghai"

    @property
    def template(self) -> TemplateConfig:
        # 函数内 import 避免 config <-> settings.manager 循环依赖
        # (manager 模块级 import config.get_config, 模块级引入会循环)。
        from application.settings.manager import register_template_callables

        return TemplateConfig(
            engine=JinjaTemplateEngine,
            engine_callback=register_template_callables,
            directory=[
                self.app_dir / "templates",
                self.app_dir / "accounts/templates",
                self.app_dir / "articles/templates",
                self.app_dir / "dashboard/templates",
                self.app_dir / "pages/templates",
                self.app_dir / "settings/templates",
                self.app_dir / "taxonomies/templates",
                self.app_dir / "themes/templates",
                self.app_dir / "seo/templates",
            ],
        )

    @property
    def compression(self) -> CompressionConfig:
        return CompressionConfig(backend="gzip")

    @property
    def openapi(self) -> OpenAPIConfig | None:
        return OpenAPIConfig(title="My API", version="1.0.0")

    @property
    def csrf(self) -> CSRFConfig:
        return CSRFConfig(secret=self.secret_key)

    @cached_property
    def tzinfo(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    @cached_property
    def stores(self) -> StoreRegistry:
        # 运行时数据目录: 响应缓存/分类缓存(FileStore) + 登录会话(session)。
        # 不止缓存, 故用 runtime 而非 caches。
        runtime_dir = self.storage_dir / "runtime"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        return StoreRegistry(
            default_factory=lambda name: FileStore(create_directories=True, path=runtime_dir).with_namespace(
                name.replace("_", "")
            )
        )

    @property
    def response_cache_config(self) -> ResponseCacheConfig:
        # 只缓存无查询参数的请求: ?page=N 等翻页变体一律不缓存,
        # 避免每个唯一 URL(含 query)都落盘成缓存文件, 也无串页风险。
        return ResponseCacheConfig(
            store="response",
            # 带查询参数(?page=N 等翻页变体)不缓存: 不落盘、不串页, 只缓存无参 path。
            # 状态码沿用默认规则: 缓存 2xx 及 301/308 永久重定向。
            cache_response_filter=(
                lambda scope, status_code: not scope.get("query_string")
                and default_do_cache_predicate(scope, status_code)
            ),
        )


@lru_cache
def get_config() -> Config:
    """
    从环境变量加载配置。
    只提取 Config 中定义的字段，忽略系统变量 (如 PATH)，避免报错。
    """
    env_data = {}
    for f in Config.__struct_fields__:
        key = f.upper()
        if key in os.environ:
            env_data[key] = os.environ[key]

    config = convert(env_data, Config, strict=False)

    # OSS 配置完整性: 三项全空=本地存储(合法), 部分填写=部署错误, 启动即报错
    oss_fields = (
        config.oss_access_key,
        config.oss_secret_key,
        config.oss_region,
        config.oss_bucket,
    )
    if any(oss_fields) and not all(oss_fields):
        raise RuntimeError("OSS 配置不完整: OSS_ACCESS_KEY/OSS_SECRET_KEY/OSS_REGION/OSS_BUCKET 必须全部配置")

    if not os.environ.get("SECRET_KEY") and not config.debug:
        raise RuntimeError("生产环境必须通过环境变量 SECRET_KEY 设置密钥")

    return config


cfg = get_config()
