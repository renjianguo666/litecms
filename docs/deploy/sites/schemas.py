from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class UploadSchema(BaseModel):
    """上传响应"""

    model_config = ConfigDict(frozen=True)

    url: str


class FileNodeSchema(BaseModel):
    """文件节点"""

    model_config = ConfigDict(frozen=True)

    name: str
    path: str
    type: str  # "file" | "directory"

    # 递归字段：Pydantic v2 自动处理引用
    # 默认为 None，表示没有子节点或不是目录
    children: list[FileNodeSchema] | None = None


class FileTreeSchema(BaseModel):
    """文件树响应"""

    model_config = ConfigDict(frozen=True)

    items: list[FileNodeSchema]


class FileContentSchema(BaseModel):
    """文件内容响应"""

    model_config = ConfigDict(frozen=True)

    path: str
    name: str
    content: str
    size: int


class TemplateRenameSchema(BaseModel):
    """重命名请求"""

    model_config = ConfigDict(frozen=True)

    name: str


class TemplateContentSchema(BaseModel):
    """模板内容请求"""

    model_config = ConfigDict(frozen=True)

    content: str
