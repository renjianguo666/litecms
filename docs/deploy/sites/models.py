from __future__ import annotations

from enum import StrEnum

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import Boolean, Integer, String, update
from sqlalchemy import Enum as SaEnum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column


class FileType(StrEnum):
    """文件类型"""

    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    OTHER = "other"


class File(UUIDv7AuditBase):
    """
    文件上传记录

    业务流程：
    1. 用户上传图片时，异步上传到 OSS，同时在此表创建记录 (is_used=False)
    2. 上传时传入 upload_token，同一次编辑会话的图片共享此 token
    3. 用户发布文章后，根据 upload_token 批量标记 is_used=True
    4. 定时任务清理 is_used=False 且超过一定时间的记录，同时删除 OSS 文件
    """

    __tablename__ = "sites_files"

    # S3/OSS 存储路径，用于删除文件
    s3_key: Mapped[str] = mapped_column(String(500), unique=True)

    # 完整访问 URL
    url: Mapped[str] = mapped_column(String(500))

    # 原始文件名
    original_name: Mapped[str] = mapped_column(String(255))

    # 文件大小（字节）
    size: Mapped[int] = mapped_column(Integer)

    # 文件类型
    file_type: Mapped[FileType] = mapped_column(
        SaEnum(FileType, native_enum=False),
        default=FileType.IMAGE,
    )

    # 是否已使用
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)

    # 上传令牌，发布时通过此 token 批量标记已使用
    upload_token: Mapped[str | None] = mapped_column(String(36), index=True)

    def __repr__(self) -> str:
        return f"<File s3_key='{self.s3_key}' file_type='{self.file_type}' is_used={self.is_used}>"

    @classmethod
    async def used(cls, session: AsyncSession, upload_token: str):
        await session.execute(
            update(cls).where(cls.upload_token == upload_token).values(is_used=True)
        )
