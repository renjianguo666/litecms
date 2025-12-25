from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from advanced_alchemy.filters import LimitOffset
from litestar import Controller, get, patch

from application.deps import create_service_provider
from application.guards import PermissionGuard

from ..schemas import PermissionSchema, PermissionUpdateSchema
from ..services import PermissionService

if TYPE_CHECKING:
    from advanced_alchemy.service import OffsetPagination


view_permission = PermissionGuard("accounts:view_permission", "查看权限")
update_permission = PermissionGuard("accounts:update_permission", "更新权限")


class PermissionController(Controller):
    path = "/permissions"
    tags = ["permissions (权限)"]

    dependencies = {"service": create_service_provider(PermissionService)}

    @get(guards=[view_permission])
    async def list_permissions(
        self,
        service: PermissionService,
        limit_offset: LimitOffset,
    ) -> OffsetPagination[PermissionSchema]:
        results, total = await service.list_and_count(limit_offset)
        return service.to_schema(
            data=results, total=total, schema_type=PermissionSchema
        )

    @patch("{item_id:uuid}", guards=[update_permission])
    async def update_permission(
        self, item_id: UUID, service: PermissionService, data: PermissionUpdateSchema
    ) -> PermissionSchema:
        item = await service.update(data, item_id)
        return service.to_schema(data=item, schema_type=PermissionSchema)
