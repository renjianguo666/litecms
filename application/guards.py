from typing import ClassVar, cast

from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from litestar.handlers.base import BaseRouteHandler

from application.accounts.models import User


class PermissionGuard:
    ALL_PERMISSIONS: ClassVar[dict[str, str | None]] = {}

    def __init__(
        self,
        permission: str,
        description: str | None = None,
    ):
        if permission not in self.ALL_PERMISSIONS:
            self.ALL_PERMISSIONS[permission] = description or permission
        self.permission = permission

    async def __call__(
        self, connection: ASGIConnection, route_handler: BaseRouteHandler
    ) -> None:
        user = cast(User, connection.user)
        if not user:
            raise NotAuthorizedException("未认证")

        # 超级用户绕过检查
        if user.is_superuser:
            return

        if not user.has_permission(self.permission):
            raise PermissionDeniedException("权限不足")

    @staticmethod
    async def permissions_to_db() -> None:
        from application.accounts.schemas import PermissionCreateSchema
        from application.accounts.services import PermissionService
        from application.config import config

        needs_commit = False

        async with config.plugins.sqlalchemy.get_session() as db_session:
            service = PermissionService(session=db_session)
            existing_perms_map = {obj.name: obj for obj in await service.list()}
            # 添加权限
            for name, description in PermissionGuard.ALL_PERMISSIONS.items():
                if name not in existing_perms_map:
                    await service.create(
                        PermissionCreateSchema(
                            name=name, description=description or ""
                        ),
                        auto_commit=False,
                    )
                    needs_commit = True

            # 清除无用的权限
            perms_set = set(PermissionGuard.ALL_PERMISSIONS.keys())
            for perm_name, perm_obj in existing_perms_map.items():
                if perm_name not in perms_set:
                    await service.delete(perm_obj.id, auto_commit=False)
                    needs_commit = True

            if needs_commit:
                await db_session.commit()
                print("Permissions updated successfully")
