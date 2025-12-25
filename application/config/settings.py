from __future__ import annotations

from functools import cached_property
from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # 不区分大小写，方便 Windows/Linux
        extra="ignore",  # 忽略 .env 中多余的配置
    )

    # ===== 基础配置 =====
    debug: bool = False
    secret_key: str = Field(
        default="insecure-dev-secret-key-change-me-in-prod",
        min_length=10,
        description="加密密钥",
    )

    # ===== 数据库配置 =====
    database_url: str = "sqlite+aiosqlite:///storage/cms.db"
    database_echo: bool = False

    # ===== URL 配置 =====
    admin_url: str = "/admin"
    admin_title: str = "LiteCMS"
    assets_url: str = "/build"
    api_prefix: str = "/api"
    api_docs_path: str = "/api/docs"

    # ===== OSS 对象存储配置 (扁平化前缀) =====
    oss_access_key: str = ""
    oss_secret_key: str = ""
    oss_endpoint: str = ""
    oss_bucket: str = ""

    # ===== 上传配置 =====
    upload_allowed_extensions: set[str] = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    upload_max_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        description="最大上传文件大小（字节）",
    )
    upload_webp_quality: int = Field(
        default=80,
        ge=1,
        le=100,
        description="WebP 压缩质量 (1-100)",
    )

    # ===== 路径计算 (Computed Fields) =====

    @computed_field
    @cached_property
    def root_dir(self) -> Path:
        """项目根目录: 假设 settings.py 在 application/config/ 下"""
        return Path(__file__).parent.parent.parent

    @computed_field
    @cached_property
    def app_dir(self) -> Path:
        return self.root_dir / "application"

    @computed_field
    @cached_property
    def template_dir(self) -> Path:
        return self.app_dir / "templates"

    @computed_field
    @cached_property
    def storage_dir(self) -> Path:
        return self.root_dir / "storage"

    @computed_field
    @cached_property
    def public_dir(self) -> Path:
        return self.root_dir / "public"

    @computed_field
    @cached_property
    def assets_dir(self) -> Path:
        return self.public_dir / "build"
