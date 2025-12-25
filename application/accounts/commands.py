from __future__ import annotations

import anyio
import click

from application.config import config

from .schemas import UserCreateSchema
from .services import UserService


@click.group(
    name="accounts",
    invoke_without_command=False,
    help="Manage application users and roles.",
)
def accounts_management() -> None:
    """Manage application users."""


@accounts_management.command(name="create-user", help="Create a new user.")
@click.option("--username", type=click.STRING)
@click.option("--email", type=click.STRING)
@click.option("--password", type=click.STRING)
@click.option("--superuser", type=click.BOOL)
def create_user(username: str, email: str, password: str, superuser: bool) -> None:
    async def _create_user(username, email, password, superuser):
        async with config.plugins.sqlalchemy.get_session() as db_session:
            service = UserService(session=db_session)
            await service.create(
                UserCreateSchema(
                    username=username,
                    email=email,
                    password=password,
                    is_superuser=superuser,
                )
            )
            await db_session.commit()
            click.echo(f"用户 {username} 创建成功！")

    username = username or click.prompt("Enter username", type=click.STRING)
    email = email or click.prompt("Enter email", type=click.STRING)
    password = password or click.prompt(
        "Enter password", type=click.STRING, hide_input=True, confirmation_prompt=True
    )
    superuser = superuser or click.prompt(
        "Create as superuser? Default: n [y/n]",
        default=False,
        show_default=False,
        type=click.BOOL,
    )
    anyio.run(_create_user, username, email, password, superuser)
