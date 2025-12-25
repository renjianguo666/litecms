from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FeatureLiteSchema(BaseModel):
    """推荐位简要信息（用于文章详情展示）"""

    # 允许从 ORM 对象读取数据
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


class FeatureSchema(FeatureLiteSchema):
    """推荐位完整信息"""

    pass


class FeatureCreateSchema(BaseModel):
    """创建推荐位"""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, max_length=100, description="推荐位名称")


class FeatureUpdateSchema(BaseModel):
    """更新推荐位"""

    model_config = ConfigDict(frozen=True)

    name: str | None = Field(min_length=1, max_length=100)
