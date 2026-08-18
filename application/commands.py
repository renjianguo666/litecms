from __future__ import annotations

from itertools import groupby

import anyio
import click
from litestar import Litestar
from litestar.plugins import CLIPlugin

from application.accounts.commands import (
    accounts_management,
    check_user_exists,
    create_user,
)
from application.guards import PermissionGuard
from application.taxonomies.commands import create_default_feature


class CommandPlugin(CLIPlugin):
    """顶层 CLI 插件，统一注册所有命令"""

    def on_cli_init(self, cli: click.Group) -> None:
        cli.add_command(accounts_management)

        @cli.command("permissions", help="显示所有已注册权限")
        def permissions(app: Litestar) -> None:
            click.echo("====== 所有权限 ======")
            perms = sorted(
                PermissionGuard.ALL_PERMISSIONS.values(),
                key=lambda x: (x["group"], x["code"]),
            )
            for group, items in groupby(perms, key=lambda x: x["group"]):
                click.echo(f"\n【{group}】")
                for p in items:
                    click.echo(f"  {p['code']} [{p['name']}]")

        @cli.command("init", help="初始化系统")
        def init(app: Litestar) -> None:

            click.echo("开始系统初始化...")
            click.echo("  步骤 1/3: 同步权限到数据库...")
            anyio.run(PermissionGuard.sync_to_db)
            click.echo(f"   ✓ 已同步 {len(PermissionGuard.ALL_PERMISSIONS)} 个权限")

            click.echo("  步骤 2/3: 预填充默认数据...")
            anyio.run(create_default_feature)
            click.echo("   ✓ 默认数据填充完成")

            click.echo("  步骤 3/3: 创建管理员账号...")

            username = click.prompt("   请输入管理员账号", type=click.STRING)

            while True:
                if not anyio.run(check_user_exists, username):
                    break
                click.echo(f"   用户 '{username}' 已存在，请重新输入。")
                username = click.prompt("   请输入管理员用户名", type=click.STRING)

            password = click.prompt(
                "   请输入管理员密码",
                type=click.STRING,
                hide_input=True,
                confirmation_prompt="   请确认管理员密码",
            )

            anyio.run(create_user, username, password)

            click.echo("   ✓ 管理员创建完成")
            click.echo("系统初始化全部完成！")
