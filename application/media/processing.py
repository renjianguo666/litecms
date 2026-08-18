from __future__ import annotations

from io import BytesIO

from litestar.concurrency import sync_to_thread
from litestar.exceptions import ValidationException
from PIL import Image

# 解压炸弹防护: PNG 无 draft 降采样, img.thumbnail() 内部 img.load() 会全量解码,
# ~89M 像素(默认 MAX_IMAGE_PIXELS)解码即吃 356MB 内存, 并发数个 OOM。
# img.size 来自 PNG header(IHDR), 读取不触发全量解码, 可在 load()/thumbnail()
# 之前按尺寸预判拒绝。max_side*2 = 6000px, 任一边超此值判定为炸弹/异常图。
_MAX_DECODE_SIDE = 6000


async def process_image(content: bytes) -> bytes:
    """图片处理管线: 线程池执行优化, 失败(非图片/损坏)转 400 拒绝。"""
    try:
        return await sync_to_thread(optimize_image, content)
    except Exception as exc:
        raise ValidationException(f"图片处理失败: {exc}") from exc


def optimize_image(content: bytes, quality: int = 82, max_side: int = 3000) -> bytes:
    """图片优化: 动图原样返回, 静态图转 WebP。

    - 动图: 转码会丢动画, 原样返回
    - 静态图: 先按尺寸上限缩小, 再全量解码转换
    """
    with Image.open(BytesIO(content)) as img:
        # 动图: 转码会丢动画, 原样返回
        if getattr(img, "is_animated", False):
            return content
        # 解压炸弹防护: img.size 来自 header 不触发全量解码, 在 thumbnail()(内部
        # load() 全量解码)之前按尺寸预判拒绝, 避免解码即吃上百 MB 内存。
        # 6000px 边长解码 ≈ 144MB, 单张可控; 超过判定为炸弹/异常图直接拒绝。
        if max(img.size) > _MAX_DECODE_SIDE:
            raise ValueError("图片尺寸过大")
        # 静态图: 先按尺寸上限缩小, 再全量解码转换
        if max(img.size) > max_side:
            img.thumbnail((max_side, max_side))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")
        output = BytesIO()
        img.save(output, format="WEBP", quality=quality, optimize=True)
        return output.getvalue()
