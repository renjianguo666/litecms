from __future__ import annotations

from advanced_alchemy.extensions.litestar.providers import create_service_provider

from application.deps import provide_services
from application.taxonomies.services import FeatureService


async def create_default_feature():
    async with provide_services(create_service_provider(FeatureService)) as (service,):
        if not await service.get_one_or_none(slug="headline"):
            await service.create({"name": "头条", "slug": "headline"})
