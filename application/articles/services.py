from __future__ import annotations

from datetime import datetime, timezone
from os.path import splitext
from typing import TYPE_CHECKING, Any, Sequence

from advanced_alchemy.filters import CollectionFilter
from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import (
    SQLAlchemyAsyncRepositoryService,
    is_dict,
    schema_dump,
)
from advanced_alchemy.service.typing import ModelDictT

from application.media.models import File
from application.taxonomies.services import (
    CategoryRepository,
    FeatureRepository,
    TagRepository,
    SpecialRepository,
)
from application.utils import build_permalink

from .models import Article, PublishStatus

if TYPE_CHECKING:
    from application.accounts.models import User


class ArticleRepository(SQLAlchemyAsyncRepository[Article]):
    model_type = Article


class ArticleService(SQLAlchemyAsyncRepositoryService[Article]):
    repository_type = ArticleRepository

    async def create_many_for_categories(
        self,
        data: ModelDictT[Article],
        creator: User,
    ) -> Sequence[Article]:
        if not is_dict(data):
            data = schema_dump(data)

        categories = await CategoryRepository(session=self.repository.session).list(
            CollectionFilter(field_name="id", values=data.pop("category_ids"))
        )

        datas = [
            {**data, "category": category, "creator": creator}
            for category in categories
        ]
        return await super().create_many(datas)

    async def to_model_on_create(
        self, data: ModelDictT[Article]
    ) -> ModelDictT[Article]:
        if not is_dict(data):
            data = schema_dump(data)

        tag_ids = data.pop("tag_ids", None)
        special_ids = data.pop("special_ids", None)
        feature_ids = data.pop("feature_ids", None)
        upload_token = data.pop("upload_token", None)

        model = await super().to_model(data)
        model.status = PublishStatus.PUBLISHED
        model.published_at = datetime.now(timezone.utc)
        model.path = build_permalink(
            rule=model.category.content_path,
            key=model.id,
            category=splitext(model.category.path)[0],
        )

        if special_ids:
            special_repo = SpecialRepository(session=self.repository.session)
            model.specials = await special_repo.list(
                CollectionFilter(field_name="id", values=special_ids)
            )

        if feature_ids:
            feature_repo = FeatureRepository(session=self.repository.session)
            model.features = await feature_repo.list(
                CollectionFilter(field_name="id", values=feature_ids)
            )

        if tag_ids:
            tag_repo = TagRepository(session=self.repository.session)
            model.tags = await tag_repo.list(
                CollectionFilter(field_name="id", values=tag_ids)
            )

        if upload_token:
            await File.used(session=self.repository.session, upload_token=upload_token)

        return model

    async def to_model_on_update(
        self, data: ModelDictT[Article]
    ) -> ModelDictT[Article]:
        if not is_dict(data):
            data = schema_dump(data)

        tags_updated_ids = data.pop("tag_ids", None)
        special_updated_ids = data.pop("special_ids", None)
        feature_updated_ids = data.pop("feature_ids", None)
        upload_token = data.pop("upload_token", None)

        data = await super().to_model(data)

        if feature_updated_ids is not None:
            feature_repo = FeatureRepository(session=self.repository.session)
            data.features = await feature_repo.list(
                CollectionFilter(field_name="id", values=feature_updated_ids)
            )

        if special_updated_ids is not None:
            special_repo = SpecialRepository(session=self.repository.session)
            data.specials = await special_repo.list(
                CollectionFilter(field_name="id", values=special_updated_ids)
            )

        if tags_updated_ids is not None:
            tag_repo = TagRepository(session=self.repository.session)
            data.tags = await tag_repo.list(
                CollectionFilter(field_name="id", values=tags_updated_ids)
            )

        if upload_token:
            await File.used(session=self.repository.session, upload_token=upload_token)

        return data

    async def update(
        self, data: ModelDictT[Article], item_id: Any | None = None, **kwargs
    ) -> Article:
        history = await self.repository.get(item_id)
        category_id = history.category_id
        category_repo = CategoryRepository(session=self.repository.session)
        category = await category_repo.get(category_id)

        kwargs["auto_commit"] = False
        model = await super().update(data, item_id, **kwargs)

        if (
            model.category != category
            and model.category.content_path != category.content_path
        ):
            model.path = build_permalink(
                rule=model.category.content_path,
                dt=model.published_at,
                key=model.id,
                category=splitext(model.category.path)[0],
            )
        await self.repository.session.commit()
        return await self.get(item_id, load=kwargs.get("load"))
