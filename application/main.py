"""
LiteCMS 服务器管理

用法:
    uv run dev      # 开发服务器（热重载）
    uv run start    # 启动生产服务（systemctl start）
    uv run stop     # 停止生产服务（systemctl stop）
    uv run deploy   # 生成部署配置文件
    uv run help     # 显示帮助信息

内部命令:
    uv run serve    # 直接运行 Granian（供 systemd 调用）

环境变量:
    PROJECT_NAME    项目名称，默认 litecms
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from granian.constants import Interfaces

load_dotenv()

PROJECT_NAME = os.getenv("PROJECT_NAME", "litecms")
PROJECT_DIR = Path(__file__).parent.parent.resolve()
DEPLOY_DIR = PROJECT_DIR / "deploy"
VENV_BIN = Path(sys.executable).parent
SOCKET_PATH = os.getenv("SOCKET_PATH", f"/tmp/{PROJECT_NAME}.sock")


# ============================================================
# 开发服务器
# ============================================================


def dev() -> None:
    """启动开发服务器（带热重载）"""
    host = os.getenv("DEV_HOST", "127.0.0.1")
    port = int(os.getenv("DEV_PORT", "8000"))

    print(f"🚀 [{PROJECT_NAME}] 开发服务器: http://{host}:{port}")
    print("   按 Ctrl+C 停止")
    print()

    try:
        from granian import Granian

        server = Granian(
            target="application:create_app",
            address=host,
            port=port,
            interface=Interfaces.ASGI,
            factory=True,
            reload=True,
        )
        server.serve()
    except KeyboardInterrupt:
        print("\n👋 已停止")
        sys.exit(0)


# ============================================================
# 生产服务（systemctl 管理）
# ============================================================


def serve() -> None:
    """直接运行 Granian（供 systemd ExecStart 调用）"""
    default_workers = max(1, (os.cpu_count() or 1) // 2)
    workers = int(os.getenv("WORKERS", str(default_workers)))

    try:
        from granian import Granian

        server = Granian(
            target="application:create_app",
            address=f"unix:{SOCKET_PATH}",
            interface=Interfaces.ASGI,
            factory=True,
            reload=False,
            workers=workers,
        )
        server.serve()
    except KeyboardInterrupt:
        sys.exit(0)


def start() -> None:
    """启动生产服务（systemctl start）"""
    try:
        subprocess.run(["sudo", "systemctl", "start", PROJECT_NAME], check=True)
        print(f"✅ [{PROJECT_NAME}] 服务已启动")
    except subprocess.CalledProcessError:
        print(f"❌ [{PROJECT_NAME}] 启动服务失败")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ systemctl 命令不可用")
        sys.exit(1)


def stop() -> None:
    """停止生产服务（systemctl stop）"""
    try:
        subprocess.run(["sudo", "systemctl", "stop", PROJECT_NAME], check=True)
        print(f"✅ [{PROJECT_NAME}] 服务已停止")
    except subprocess.CalledProcessError:
        print(f"❌ [{PROJECT_NAME}] 停止服务失败")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ systemctl 命令不可用")
        sys.exit(1)


# ============================================================
# 部署配置生成
# ============================================================


def deploy() -> None:
    """生成部署配置文件"""
    user = os.getenv("DEPLOY_USER", "www-data")
    group = os.getenv("DEPLOY_GROUP", user)
    domain = os.getenv("DOMAIN", "example.com")

    DEPLOY_DIR.mkdir(exist_ok=True)

    # 1. systemd service
    service_content = f"""\
[Unit]
Description={PROJECT_NAME.title()} Application
After=network.target postgresql.service

[Service]
Type=simple
User={user}
Group={group}
WorkingDirectory={PROJECT_DIR}
Environment="PATH={VENV_BIN}"
ExecStart={VENV_BIN}/serve
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    service_file = DEPLOY_DIR / f"{PROJECT_NAME}.service"
    service_file.write_text(service_content, encoding="utf-8")

    # 2. Nginx 配置
    nginx_content = f"""\
upstream {PROJECT_NAME}_backend {{
    server unix:{SOCKET_PATH};
    keepalive 32;
}}

server {{
    listen 80;
    server_name {domain};

    location /assets {{
        alias {PROJECT_DIR}/public;
        expires 30d;
    }}

    location / {{
        proxy_pass http://{PROJECT_NAME}_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }}
}}
"""
    nginx_file = DEPLOY_DIR / "nginx.conf"
    nginx_file.write_text(nginx_content, encoding="utf-8")

    # 输出结果
    print(f"📦 [{PROJECT_NAME}] 部署配置已生成:")
    print(f"   ✅ deploy/{PROJECT_NAME}.service")
    print("   ✅ deploy/nginx.conf")
    print()
    print("部署步骤:")
    print("   1. cp .env.example .env && vim .env")
    print(f"   2. sudo cp deploy/{PROJECT_NAME}.service /etc/systemd/system/")
    print(f"   3. sudo systemctl enable --now {PROJECT_NAME}")
    print(f"   4. sudo cp deploy/nginx.conf /etc/nginx/sites-enabled/{PROJECT_NAME}")
    print("   5. sudo nginx -t && sudo systemctl reload nginx")


# ============================================================
# 帮助信息
# ============================================================


def help() -> None:
    """显示命令帮助信息"""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    {PROJECT_NAME.upper()} 服务器管理
╚══════════════════════════════════════════════════════════════╝

开发命令:
─────────────────────────────────────────────────────────────────
  uv run dev        启动开发服务器（热重载）
                    本地开发时使用，修改代码自动重启

部署命令:
─────────────────────────────────────────────────────────────────
  uv run deploy     生成部署配置文件
                    生成 systemd、nginx 配置到 deploy/ 目录

生产命令:
─────────────────────────────────────────────────────────────────
  uv run start      启动生产服务 (systemctl start {PROJECT_NAME})
  uv run stop       停止生产服务 (systemctl stop {PROJECT_NAME})
  uv run serve      直接运行 Granian（供 systemd 调用，一般不手动执行）

环境变量:
─────────────────────────────────────────────────────────────────
  PROJECT_NAME      项目名称，默认 litecms
  SOCKET_PATH       Socket 路径，默认 /tmp/{{PROJECT_NAME}}.sock
  WORKERS           Worker 进程数，默认 CPU 核心数
  DEV_HOST          开发服务器地址，默认 127.0.0.1
  DEV_PORT          开发服务器端口，默认 8000
""")
