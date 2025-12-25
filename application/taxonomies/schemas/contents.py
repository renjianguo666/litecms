"""
Contents 相关 Schema

用于 Features/Tags/Specials 的内容关联管理
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PushContentsSchema(BaseModel):
    """添加内容请求体"""

    model_config = ConfigDict(frozen=True)

    content_ids: list[UUID] = Field(..., min_length=1, description="内容ID列表")


class PushContentsResponseSchema(BaseModel):
    """添加内容响应"""

    model_config = ConfigDict(frozen=True)

    added: int = Field(..., description="成功添加数量")
    total_requested: int = Field(..., description="请求添加数量")


class ContentItemSchema(BaseModel):
    """内容条目基础信息"""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    content_id: UUID = Field(..., description="内容ID")
    title: str = Field(..., description="内容标题")


# ============================================================
# Feature Contents Schema
# ============================================================


class FeatureContentItem(ContentItemSchema):
    """推荐位内内容条目"""

    pass


class FeatureContentsResponse(BaseModel):
    """推荐位内容列表响应"""

    model_config = ConfigDict(frozen=True)

    feature_id: UUID = Field(..., description="推荐位ID")
    name: str = Field(..., description="推荐位名称")
    contents: list[FeatureContentItem] = Field(
        default_factory=list, description="内容列表"
    )


# ============================================================
# Tag Contents Schema
# ============================================================


class TagContentItem(ContentItemSchema):
    """标签内内容条目"""

    pass


class TagContentsResponse(BaseModel):
    """标签内容列表响应"""

    model_config = ConfigDict(frozen=True)

    tag_id: UUID = Field(..., description="标签ID")
    name: str = Field(..., description="标签名称")
    slug: str = Field(..., description="标签标识")
    contents: list[TagContentItem] = Field(default_factory=list, description="内容列表")


# ============================================================
# Special Contents Schema
# ============================================================


class SpecialContentItem(ContentItemSchema):
    """专题内内容条目"""

    position: int = Field(..., description="排序位置")
    headline: bool = Field(..., description="是否头条")
    added_at: datetime = Field(..., description="添加时间")


class SpecialContentsResponse(BaseModel):
    """专题内容列表响应"""

    model_config = ConfigDict(frozen=True)

    special_id: UUID = Field(..., description="专题ID")
    name: str = Field(..., description="专题名称")
    slug: str = Field(..., description="专题标识")
    title: str = Field(..., description="专题标题")
    description: str | None = Field(description="专题描述")
    cover_url: str | None = Field(description="封面图片URL")
    contents: list[SpecialContentItem] = Field(
        default_factory=list, description="内容列表"
    )


class SortItemSchema(BaseModel):
    """排序项"""

    model_config = ConfigDict(frozen=True)

    content_id: UUID = Field(..., description="内容ID")
    position: int = Field(..., ge=0, description="排序位置")


class SortContentsSchema(BaseModel):
    """批量排序请求体"""

    model_config = ConfigDict(frozen=True)

    items: list[SortItemSchema] = Field(..., description="排序项列表")


class SortContentsResponseSchema(BaseModel):
    """排序响应"""

    model_config = ConfigDict(frozen=True)

    updated: int = Field(..., description="更新数量")
