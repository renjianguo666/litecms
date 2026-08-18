from __future__ import annotations

from urllib.parse import urljoin

import aiohttp
from litestar.datastructures import UploadFile
from litestar.exceptions import ValidationException

from application.config import cfg
from application.settings import SettingField, SettingRegistry

from .processing import process_image
from .ssrf import MAX_REDIRECTS, PinningResolver, validate_url
from .storage import get_storage

# 注册媒体上传配置(模块导入即注册,类似 PermissionGuard)
SettingRegistry.register(
    SettingField(
        key="upload_allowed_extensions",
        label="允许上传的图片格式",
        field_type="list",
        default=[".jpg", ".jpeg", ".png", ".gif", ".webp"],
        description="逗号分隔的扩展名列表",
        group="媒体",
    )
)

DOWNLOAD_TIMEOUT = 10  # aiohttp 网络超时(秒),防止卡死

# 伪装主流桌面 Chrome UA: 多数图床/CDN 只认 Mozilla 开头, 非浏览器 UA 易被拒(403)。
#
# 版本号写死, 平时无需维护(图床只认 Mozilla 形状, 不校验具体大版本)。
# 仅当某天外链图片拉取失败、报错诡异、且网络/超时/SSRF 层都正常时,
# 才怀疑 UA 过旧被目标站点拒——到此处更新为较新的 Chrome 版本号即可。
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# 增量读取块大小: 平衡系统调用次数与内存占用
_CHUNK_SIZE = 64 * 1024


async def upload_image(file: UploadFile) -> str:
    """本地图片上传: 动图原样存, 静态图转 WebP 后存储, 返回 URL。

    输入扩展名校验在控制器层(请求层), 此处格式由转码管线实测兜底。
    大小限制由 Litestar request_max_body_size 统一拦截。
    """
    content = await file.read()
    processed = await process_image(content)
    try:
        return await get_storage().save(processed)
    except Exception:
        # OSS put_object(网络/鉴权/桶) 与本地 write_bytes(盘满/权限) 抛原生异常,
        # 控制器只注册 ValidationException→JSON, 裸抛会落全局 500 返回 HTML。
        # 转 ValidationException 走 JSON, 不回显内部细节。
        raise ValidationException("图片存储失败") from None


async def download_image(url: str) -> str:
    """外链图片转存: SSRF 校验后下载, 与上传同一转码管线, 存储后返回 URL。"""
    content = await _fetch_remote_image(url)
    processed = await process_image(content)
    try:
        return await get_storage().save(processed)
    except Exception:
        raise ValidationException("图片存储失败") from None


async def _fetch_remote_image(url: str) -> bytes:
    """下载辅助: 连接级 SSRF 校验(PinningResolver) + 逐跳重定向 + 大小限制。

    - DNS 解析与内网校验在 aiohttp 建连时由 PinningResolver 完成, 校验与连接
      同一处, 消除 DNS rebinding TOCTOU; TLS SNI/证书仍用 URL 域名。
    - 手动跟重定向, 每跳过 validate_url(scheme) + 连接时 IP 校验。
    - 远端 4xx/5xx 与连接错误统一走 ValidationException, 不裸抛 500。
    - 增量读 body, 超限即断, 不全量载入内存。

    格式校验由转码管线(_process_image)统一承担。
    """
    max_size = cfg.request_max_body_size
    current_url = await validate_url(url)

    connector = aiohttp.TCPConnector(resolver=PinningResolver())
    timeout = aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT)
    headers = {"User-Agent": _USER_AGENT}
    async with aiohttp.ClientSession(
        connector=connector, timeout=timeout, headers=headers
    ) as session:
        for _ in range(MAX_REDIRECTS):
            try:
                # allow_redirects=False: 手动处理重定向, 每跳做 scheme + IP 校验
                async with session.get(current_url, allow_redirects=False) as resp:
                    # 手动跟重定向，每一跳都校验目标地址
                    if resp.status in (301, 302, 303, 307, 308):
                        location = resp.headers.get("location", "")
                        if not location:
                            raise ValidationException("重定向缺少目标地址")
                        # 先拼成绝对 URL（处理相对路径重定向），再校验 scheme
                        current_url = await validate_url(urljoin(current_url, location))
                        continue

                    # 纳入 try/except: 远端 4xx/5xx 走 ValidationException, 不裸抛 500
                    resp.raise_for_status()

                    # 增量读, 边读边累计, 超限即断 (不全量加载进内存)
                    chunks: list[bytes] = []
                    total = 0
                    async for chunk in resp.content.iter_chunked(_CHUNK_SIZE):
                        total += len(chunk)
                        if total > max_size:
                            raise ValidationException("图片超过大小限制")
                        chunks.append(chunk)
                    return b"".join(chunks)
            except (aiohttp.ClientError, TimeoutError) as e:
                raise ValidationException(f"下载失败: {e}") from e

        raise ValidationException("重定向次数过多")
