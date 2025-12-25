#!/bin/bash
# litecms 一键部署脚本
# 用法: sudo bash install.sh

set -e

PROJECT_NAME="litecms"
PROJECT_DIR="/var/www/litecms"
DEPLOY_DIR="/var/www/litecms/deploy"

echo "🚀 开始部署 $PROJECT_NAME..."

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用 sudo 运行此脚本"
    exit 1
fi

# 1. 安装 systemd 服务
echo "📦 安装 systemd 服务..."
cp "$DEPLOY_DIR/$PROJECT_NAME.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable $PROJECT_NAME

# 2. 安装 Nginx 配置
if command -v nginx &> /dev/null; then
    echo "📦 安装 Nginx 配置..."
    cp "$DEPLOY_DIR/nginx.conf" /etc/nginx/sites-available/$PROJECT_NAME
    ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
else
    echo "⚠️  Nginx 未安装，跳过配置"
fi

# 3. 复制环境变量模板
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "📦 复制环境变量模板..."
    cp "$DEPLOY_DIR/.env.production" "$PROJECT_DIR/.env"
    echo "⚠️  请编辑 $PROJECT_DIR/.env 填写真实配置"
fi

echo ""
echo "✅ 部署完成！"
echo ""
echo "下一步操作:"
echo "  1. 编辑配置: vim $PROJECT_DIR/.env"
echo "  2. 启动服务: systemctl start $PROJECT_NAME"
echo "  3. 查看状态: systemctl status $PROJECT_NAME"
echo "  4. 查看日志: journalctl -u $PROJECT_NAME -f"
