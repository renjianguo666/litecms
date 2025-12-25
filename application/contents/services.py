from advanced_alchemy.repository import SQLAlchemyAsyncRepository
from advanced_alchemy.service import SQLAlchemyAsyncRepositoryService

from .models import Content


class ContentRepository(SQLAlchemyAsyncRepository[Content]):
    model_type = Content


class ContentService(SQLAlchemyAsyncRepositoryService[Content]):
    repository_type = ContentRepository
