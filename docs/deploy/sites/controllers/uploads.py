import oss2
from io import BytesIO
from litestar import Controller, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body
from pathlib import Path
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils import uuid7
from yarl import URL

from application.config import config

from ..models import File
from ..schemas import UploadSchema


def compress_image_to_webp(file_content: bytes, quality: int = 80) -> bytes:
    """将图片压缩为 WebP 格式"""
    with Image.open(BytesIO(file_content)) as img:
        # 处理 RGBA 模式（PNG 透明背景）
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        # 保存为 WebP
        output = BytesIO()
        img.save(output, format="WEBP", quality=quality, optimize=True)
        return output.getvalue()


class UploadController(Controller):
    path = "/upload"
    tags = ["Upload (文件上传)"]

    @post()
    async def upload(
        self,
        db_session: AsyncSession,
        data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
        upload_token: str = Body(),
    ) -> UploadSchema:
        """上传文件到 OSS"""
        # 验证 upload_token
        if not upload_token:
            raise HTTPException(status_code=400, detail="upload_token is required")

        # 验证文件扩展名
        ext = Path(data.filename or "").suffix.lower()
        if ext not in config.upload_allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {ext}，允许: {', '.join(config.upload_allowed_extensions)}",
            )

        # 读取文件内容
        file_content = await data.read()

        # 验证文件大小（压缩前）
        if len(file_content) > config.upload_max_size:
            max_mb = config.upload_max_size / (1024 * 1024)
            raise HTTPException(
                status_code=400, detail=f"文件大小超过限制 ({max_mb:.0f}MB)"
            )

        # 压缩图片为 WebP 格式
        try:
            file_content = compress_image_to_webp(
                file_content, quality=config.upload_webp_quality
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"图片处理失败: {e}")

        # OSS 配置
        bucket_name = config.oss_bucket
        auth = oss2.Auth(config.oss_access_key, config.oss_secret_key)
        bucket = oss2.Bucket(auth, config.oss_endpoint, bucket_name)

        s3_key = f"images/{uuid7().hex}.webp"  # 统一使用 .webp 扩展名

        # 上传到 OSS
        try:
            bucket.put_object(s3_key, file_content)
        except oss2.exceptions.OssError as e:
            raise HTTPException(status_code=500, detail=f"上传失败: {e.message}")

        # 返回访问 URL
        # 解析 endpoint 获取 host，拼接 bucket 和路径
        endpoint_url = URL(config.oss_endpoint)
        url = str(
            URL.build(
                scheme="https",
                host=f"{bucket_name}.{endpoint_url.host}",
                path=f"/{s3_key}",
            )
        )

        # 写入数据库
        db_session.add(
            File(
                url=url,
                s3_key=s3_key,
                original_name=data.filename or "unknown",
                size=len(file_content),
                upload_token=upload_token,
            )
        )
        await db_session.commit()

        return UploadSchema(url=url)
