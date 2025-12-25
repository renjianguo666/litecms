from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from application.accounts.schemas import UserLiteSchema
from application.contents.enums import PublishStatus
from application.taxonomies.schemas import (
    CategoryLiteSchema,
    FeatureLiteSchema,
    SpecialLiteSchema,
    TagLiteSchema,
)


class ArticleLiteSchema(BaseModel):
    """文章列表项（轻量）"""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    title: str
    url: str
    description: str | None = None
    cover_url: str | None = None
    source: str | None = None
    author: str | None = None
    status: PublishStatus
    views: int
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    category_id: UUID
    category: CategoryLiteSchema
    creator_id: UUID
    creator: UserLiteSchema


class ArticleSchema(ArticleLiteSchema):
    text: str
    tags: list[TagLiteSchema]
    specials: list[SpecialLiteSchema]
    features: list[FeatureLiteSchema]


class ArticleCreateSchema(BaseModel):
    """创建文章"""

    model_config = ConfigDict(frozen=True)

    # 必填字段
    title: str = Field(..., min_length=1, max_length=255, description="文章标题")
    category_ids: list[UUID] = Field(..., min_length=1, description="所属栏目ID列表")
    text: str = Field(..., min_length=1, description="文章内容")

    description: str | None = Field(
        default=None, max_length=500, description="文章摘要"
    )
    cover_url: str | None = Field(
        default=None, max_length=255, description="封面图片URL"
    )
    source: str | None = Field(default=None, max_length=200, description="文章来源")
    author: str | None = Field(default=None, max_length=100, description="作者")
    status: PublishStatus | None = Field(default=None, description="发布状态")
    published_at: datetime | None = Field(
        default=None, description="发布时间，留空则使用当前时间"
    )
    tag_ids: list[UUID] | None = Field(default=None, description="标签ID列表")
    special_ids: list[UUID] | None = Field(default=None, description="专题ID列表")
    feature_ids: list[UUID] | None = Field(default=None, description="推荐位ID列表")
    upload_token: str | None = Field(
        default=None, max_length=36, description="上传令牌，用于标记图片已使用"
    )


class ArticleUpdateSchema(BaseModel):
    """更新文章"""

    model_config = ConfigDict(frozen=True)

    # 在 Pydantic 中，对于更新模型（PATCH），我们将所有字段设为 Optional。
    # 在业务逻辑中，请使用 article_update.model_dump(exclude_unset=True)
    # 来获取仅包含前端传递了的字段，从而实现 "UNSET" 的效果。

    title: str | None = Field(
        default=None, min_length=1, max_length=255, description="文章标题"
    )
    category_id: UUID | None = Field(default=None, description="所属栏目ID")
    text: str | None = Field(default=None, min_length=1, description="文章内容")

    description: str | None = Field(
        default=None, max_length=500, description="文章摘要"
    )
    cover_url: str | None = Field(
        default=None, max_length=255, description="封面图片URL"
    )
    source: str | None = Field(default=None, max_length=200, description="文章来源")
    author: str | None = Field(default=None, max_length=100, description="作者")
    status: PublishStatus | None = Field(default=None, description="发布状态")
    published_at: datetime | None = Field(default=None, description="发布时间")
    tag_ids: list[UUID] | None = Field(default=None, description="标签ID列表")
    special_ids: list[UUID] | None = Field(default=None, description="专题ID列表")
    feature_ids: list[UUID] | None = Field(default=None, description="推荐位ID列表")
    upload_token: str | None = Field(
        default=None, max_length=36, description="上传令牌，用于标记图片已使用"
    )
