from __future__ import annotations

import anyio
import click
from advanced_alchemy.extensions.litestar.providers import create_service_provider

from application.accounts.services import UserService
from application.deps import provide_services


@click.group(
    name="accounts",
    invoke_without_command=False,
    help="用户与角色管理",
)
def accounts_management() -> None:
    """用户与角色管理命令组"""


@accounts_management.command(name="create", help="创建管理员")
@click.option("--username", "-u", type=click.STRING)
@click.option("--password", "-p", type=click.STRING)
def create_user_command(username: str, password: str) -> None:
    """创建后台用户（默认超级用户）。"""
    username = username or str(click.prompt("请输入管理员账号", type=click.STRING))

    while True:
        if not anyio.run(check_user_exists, username):
            break
        click.echo(f"用户 '{username}' 已存在，请重新输入。")
        username = click.prompt("请输入管理员用户名", type=click.STRING)

    password = password or str(
        click.prompt(
            "请输入管理员密码",
            type=click.STRING,
            hide_input=True,
            confirmation_prompt="请确认管理员密码",
        )
    )

    anyio.run(create_user, username, password)

    click.echo(f"用户 '{username}' 创建成功！")


async def check_user_exists(username: str) -> bool:
    async with provide_services(create_service_provider(UserService)) as (service,):
        return await service.get_one_or_none(username=username)


async def create_user(username: str, password: str, superuser: bool = True) -> None:
    async with provide_services(create_service_provider(UserService)) as (service,):
        data: dict = {
            "username": username,
            "password_hash": password,
            "is_superuser": superuser,
            "is_active": True,
        }
        await service.create(data)
