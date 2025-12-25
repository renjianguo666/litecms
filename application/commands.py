from __future__ import annotations

import json
import anyio
import click
from litestar import Litestar
from litestar.plugins import CLIPluginProtocol

from application.accounts.commands import accounts_management

from .guards import PermissionGuard


class CommandPlugin(CLIPluginProtocol):
    def on_cli_init(self, cli: click.Group) -> None:
        cli.add_command(accounts_management)

        @cli.command("permissions", help="显示所有权限")
        def run(app: Litestar):
            click.echo("======所有权限======")
            for perm, desc in PermissionGuard.ALL_PERMISSIONS.items():
                desc = f" [{desc}]" if desc else ""
                click.echo(f"|--->{perm}{desc}")

        @cli.command("init")
        def init(app: Litestar):
            anyio.run(PermissionGuard.permissions_to_db)
            click.echo("Application initialized successfully.")

        @cli.command("demo")
        def demo(app: Litestar):
            from application.taxonomies.models import Category

            cate = Category(
                name="name",
                title="title",
                path="/demo",
                content_path="/p/{key}.html",
            )
            click.echo(json.dumps(cate.to_dict(), indent=2, ensure_ascii=False))
