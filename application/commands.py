from __future__ import annotations

import os
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
from application.config import cfg
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

        @cli.command("ok")
        def ok(app: Litestar) -> None:
            print("==", cfg.root_dir.name)

            venv_bin = cfg.root_dir / ".venv" / "bin"
            granian_exe = venv_bin / "granian"

            print(granian_exe)

        @cli.command("deploy", help="生成 systemd 和 Nginx 配置文件（手动部署）")
        @click.option("--domain", required=True, help="部署域名")
        def deploy(app: Litestar, domain: str) -> None:

            # 通过环境变量或默认值（灵活配置）
            # SUDO_USER 优先: sudo 执行时 USER=root, 会以 root 跑 granian; 用真实登录用户更安全。
            user = os.getenv("SUDO_USER") or os.getenv("USER") or "root"
            group = user

            project_name = cfg.root_dir.name
            venv_bin = cfg.root_dir / ".venv" / "bin"
            granian_exe = venv_bin / "granian"

            if not granian_exe.exists():
                click.echo(
                    f"❌ 未找到 {granian_exe}，请确保虚拟环境已安装 granian", err=True
                )
                return

            sock_path = f"/tmp/{project_name}.sock"
            deploy_dir = cfg.storage_dir / "deploy"
            deploy_dir.mkdir(exist_ok=True)

            # 1. 生成 systemd service
            exec_start = (
                f"{granian_exe} --interface asgi --factory --workers 1 "
                f"--uds {sock_path} --uds-permissions 666 application:create_app"
            )
            service_content = f"""\
[Unit]
Description={project_name.title()} Application
After=network.target

[Service]
Type=simple
User={user}
Group={group}
WorkingDirectory={cfg.root_dir}
# 进程被 OOM 杀/崩溃时不会 unlink socket, 残留会导致下次绑定失败;
# ExecStartPre 启动前先清掉, 避免 Restart=always 无限重启崩溃循环。
ExecStartPre=/bin/rm -f {sock_path}
ExecStart={exec_start}
Restart=always
RestartSec=5
MemoryHigh=550M
MemoryMax=800M


[Install]
WantedBy=multi-user.target
        """
            (deploy_dir / f"{project_name}.service").write_text(service_content)

            # 2. 生成 Nginx 配置
            nginx_content = f"""\
upstream {project_name}_backend {{
    server unix:{sock_path};
    keepalive 32;
}}

server {{
    listen 80;
    server_name {domain};

    # 与应用 request_max_body_size 对齐(默认 1m 会挡掉图片上传)
    client_max_body_size 10m;

    # 静态资源/上传直接由 nginx 从 public/ 出, 其余走后端
    root {cfg.public_dir};

    location /static {{
        expires 30d;
    }}

    location / {{
        try_files $uri @{project_name}_backend;
    }}

    location @{project_name}_backend {{
        proxy_pass http://{project_name}_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
        """
            (deploy_dir / "nginx.conf").write_text(nginx_content)

            click.echo(f"✅ 配置文件已生成至 {deploy_dir}")
            click.echo("\n📌 手动部署步骤：")
            click.echo("  1. 复制 systemd 服务并启用：")
            click.echo(
                f"     sudo cp {deploy_dir}/{project_name}.service /etc/systemd/system/"
            )
            click.echo("     sudo systemctl daemon-reload")
            click.echo(f"     sudo systemctl enable --now {project_name}")
            click.echo("  2. 复制 Nginx 配置并重载：")
            click.echo(
                f"     sudo cp {deploy_dir}/nginx.conf /etc/nginx/sites-enabled/{project_name}"
            )
            click.echo("     sudo nginx -t && sudo systemctl reload nginx")
            click.echo("  3. 查看状态/日志：")
            click.echo(f"     sudo systemctl status {project_name}")
            click.echo(f"     sudo journalctl -u {project_name} -f")
