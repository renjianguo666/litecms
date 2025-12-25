from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class UploadSchema(BaseModel):
    """上传响应"""

    model_config = ConfigDict(frozen=True)

    url: str
