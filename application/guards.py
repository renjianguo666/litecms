"""权限守卫

PermissionGuard 实例化时自动注册权限到 ALL_PERMISSIONS，
通过 ``litestar init`` 命令同步到数据库。
"""

from __future__ import annotations

from typing import ClassVar, TypedDict, cast

from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException, PermissionDeniedException
from litestar.handlers import BaseRouteHandler

from application.accounts.models import User


class PermissionInfo(TypedDict):
    """权限元信息"""

    code: str
    name: str
    group: str


class PermissionGuard:
    """权限守卫，实例化时自动注册权限"""

    ALL_PERMISSIONS: ClassVar[dict[str, PermissionInfo]] = {}

    def __init__(self, code: str, name: str, group: str) -> None:
        self.code = code
        PermissionGuard.ALL_PERMISSIONS.setdefault(
            code,
            PermissionInfo(code=code, name=name, group=group),
        )

    def __call__(self, connection: ASGIConnection, _: BaseRouteHandler) -> None:
        user = cast(User, connection.user)
        if not user:
            raise NotAuthorizedException("未认证")

        if user.is_superuser:
            return

        if not user.has_permission(self.code):
            raise PermissionDeniedException("权限不足")

    @staticmethod
    async def sync_to_db() -> None:
        """将 ALL_PERMISSIONS 同步到数据库

        - 代码新增的权限: INSERT
        - 代码删除的权限: DELETE (CASCADE 清理角色-权限关联)
        - 名称/分组变更: UPDATE
        """
        from sqlalchemy import select

        from application.accounts.models import Permission
        from application.database import sqlalchemy_config

        session_maker = sqlalchemy_config.create_session_maker()
        async with session_maker() as session:
            existing = {
                p.code: p for p in (await session.scalars(select(Permission))).all()
            }

            for code, info in PermissionGuard.ALL_PERMISSIONS.items():
                if code not in existing:
                    session.add(
                        Permission(
                            code=info["code"],
                            name=info["name"],
                            group=info["group"],
                        )
                    )
                else:
                    existing[code].name = info["name"]
                    existing[code].group = info["group"]

            code_perms = set(PermissionGuard.ALL_PERMISSIONS.keys())
            for code, perm in existing.items():
                if code not in code_perms:
                    await session.delete(perm)

            await session.commit()
