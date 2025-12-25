from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TemplateRenameSchema(BaseModel):
    """重命名请求"""

    model_config = ConfigDict(frozen=True)

    name: str


class TemplateContentSchema(BaseModel):
    """模板内容请求"""

    model_config = ConfigDict(frozen=True)

    content: str
