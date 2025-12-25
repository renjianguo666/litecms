from __future__ import annotations

from typing import TYPE_CHECKING

from litestar.stores.file import FileStore
from litestar.stores.registry import StoreRegistry

if TYPE_CHECKING:
    from .settings import Settings


def create_stores_config(settings: Settings) -> StoreRegistry:
    return StoreRegistry(
        default_factory=lambda name: FileStore(
            create_directories=True, path=settings.storage_dir / "caches"
        ).with_namespace(name.replace("_", ""))
    )
