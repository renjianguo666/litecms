from __future__ import annotations

from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Protocol
from urllib.parse import urljoin
from uuid import uuid7

from alibabacloud_oss_v2 import Config as OSSConfig
from alibabacloud_oss_v2 import GetBucketInfoRequest as OSSGetBucketInfoRequest
from alibabacloud_oss_v2 import PutObjectRequest as OSSPutObjectRequest
from alibabacloud_oss_v2.aio import AsyncClient as OSSAsyncClient
from alibabacloud_oss_v2.credentials import (
    StaticCredentialsProvider as OSSCredentialsProvider,
)
from litestar.concurrency import sync_to_thread

from application.config import cfg


class Storage(Protocol):
    async def save(self, content: bytes) -> str: ...


def _detect_ext(content: bytes) -> str:
    """从文件头推断格式(转码层产出 WebP/GIF/PNG)"""
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return ".webp"
    if content.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if content.startswith(b"\x89PNG"):
        return ".png"
    return ""


def _generate_key(ext: str) -> str:
    """生成 年/月/uuid7.ext 形式的存储 key,uuid7 天然按时间排序"""
    now = datetime.now(cfg.tzinfo)
    filename = f"{uuid7().hex}{ext}"
    return f"{now.year}{now.month:02d}/{filename}"


class LocalStorage:
    """本地磁盘存储,通过 /uploads 静态路由对外访问"""

    def __init__(self, upload_root: Path) -> None:
        self.upload_root = upload_root

    async def save(self, content: bytes) -> str:
        key = _generate_key(_detect_ext(content))
        file_path = self.upload_root / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # 磁盘 IO 放线程池,避免阻塞事件循环
        await sync_to_thread(file_path.write_bytes, content)
        return f"/uploads/{key}"


class OSSStorage:
    """阿里云 OSS 存储,走 ECS 内网 endpoint 免流量费"""

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        region: str,
        bucket: str,
        prefix: str,
        cdn_url: str,
        use_internal: bool = True,
    ) -> None:
        self.client = OSSAsyncClient(
            OSSConfig(
                region=region,
                credentials_provider=OSSCredentialsProvider(access_key, secret_key),
                use_internal_endpoint=use_internal,
            )
        )
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.cdn_url = cdn_url.rstrip("/")
        # 未配 CDN 时兜底的 bucket 公网域名(懒加载缓存, 官方 extranet_endpoint)
        self._bucket_url: str | None = None

    async def get_bucket_url(self) -> str:
        """获取 bucket 公网域名(浏览器可访问), 官方 extranet_endpoint, 首次调用缓存。"""
        if self._bucket_url is None:
            resp = await self.client.get_bucket_info(OSSGetBucketInfoRequest(bucket=self.bucket))
            bucket_info = resp.bucket_info
            if bucket_info is None:
                raise RuntimeError(f"GetBucketInfo 未返回 bucket 信息: {self.bucket}")
            self._bucket_url = f"https://{bucket_info.extranet_endpoint}"
        return self._bucket_url

    async def save(self, content: bytes) -> str:
        key = _generate_key(_detect_ext(content))
        full_key = f"{self.prefix}/{key}" if self.prefix else key
        await self.client.put_object(OSSPutObjectRequest(bucket=self.bucket, key=full_key, body=content))
        # 配了 CDN 用 CDN; 未配回退 bucket 公网域名(官方 extranet_endpoint)
        return urljoin(self.cdn_url or await self.get_bucket_url(), full_key)


@lru_cache
def get_storage() -> Storage:
    """存储后端选择,结果缓存,进程内只构造一次。

    三态逻辑:
    - 四项全填 -> OSS
    - 全空     -> 本地磁盘
    - 部分填   -> 配置不完整, 启动即报错(避免静默走错后端)
    """
    oss_config = (
        cfg.oss_access_key,
        cfg.oss_secret_key,
        cfg.oss_region,
        cfg.oss_bucket,
    )
    if all(oss_config):
        return OSSStorage(
            access_key=cfg.oss_access_key,
            secret_key=cfg.oss_secret_key,
            region=cfg.oss_region,
            bucket=cfg.oss_bucket,
            prefix=cfg.oss_prefix,
            cdn_url=cfg.oss_cdn_url,
            use_internal=cfg.oss_use_internal,
        )
    if any(oss_config):
        raise RuntimeError("OSS 配置不完整: OSS_ACCESS_KEY/OSS_SECRET_KEY/OSS_REGION/OSS_BUCKET 必须全部配置")
    return LocalStorage(upload_root=cfg.public_dir / "uploads")


async def close_storage() -> None:
    """应用关闭时清理 OSS 客户端连接池。

    get_storage() 用 @lru_cache 进程级单例, OSSAsyncClient 内部持有连接池/HTTP
    session, 常驻运行无碍, 但 shutdown/热重载时无清理会泄漏。LocalStorage 无资源
    需释放。仅在已构造过 OSSStorage 时调用 close。
    """
    if not _HAVE_OSS:
        return
    try:
        storage = get_storage()
    except Exception:
        return
    if isinstance(storage, OSSStorage):
        await storage.client.close()


# 是否配置了 OSS(决定 close_storage 是否需要做事)
_HAVE_OSS = all(
    (
        cfg.oss_access_key,
        cfg.oss_secret_key,
        cfg.oss_region,
        cfg.oss_bucket,
    )
)
