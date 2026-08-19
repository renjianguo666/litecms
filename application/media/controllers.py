from __future__ import annotations

from pathlib import Path

from litestar import Controller, Request, Response, post
from litestar.datastructures import UploadFile
from litestar.exceptions import ValidationException
from litestar.params import MultipartBody
from litestar.status_codes import HTTP_400_BAD_REQUEST
from msgspec import Struct

from application.guards import PermissionGuard
from application.settings import get_settings

from .services import download_image, upload_image

upload_permission = PermissionGuard("media:upload", "上传附件", "文章管理")


class UploadFormData(Struct):
    """上传请求体,file 和 url 二选一"""

    file: UploadFile | None = None
    url: str = ""


class UploadResult(Struct):
    """图片上传成功响应"""

    url: str


class ErrorResponse(Struct):
    """错误响应"""

    message: str


def validation_json_handler(
    request: Request, exc: ValidationException
) -> Response[ErrorResponse]:
    """media 接口的 ValidationException 返回 JSON,不走全局 HTML 渲染"""
    return Response(
        content=ErrorResponse(message=exc.detail),
        status_code=HTTP_400_BAD_REQUEST,
    )


class MediaController(Controller):
    path = "/media"
    include_in_schema = True
    exception_handlers = {ValidationException: validation_json_handler}

    @post("/upload", name="media:upload", guards=[upload_permission])
    async def upload(
        self,
        data: MultipartBody[UploadFormData],
    ) -> UploadResult:
        """图片上传接口

        两种用法:
        - 上传文件: multipart/form-data, 字段 file
        - 转存外链: multipart/form-data, 字段 url

        成功返回 UploadResult(200),失败返回 ErrorResponse(400)
        """
        if data.url:
            url = await download_image(data.url)
        elif data.file:
            # 输入校验(请求层, 类比其他模块的 WTForms 校验): 扩展名白名单快速失败
            filename = data.file.filename or "upload.bin"
            ext = Path(filename).suffix.lower()
            if ext not in get_settings("upload_allowed_extensions"):
                raise ValidationException(f"不支持的图片格式: {ext}")
            url = await upload_image(data.file)
        else:
            raise ValidationException("缺少 file 或 url 字段")

        return UploadResult(url=url)
