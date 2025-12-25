# 前端打包与部署指南

## 概述

本文档描述了前端资源（Vite + Solid.js）的打包和部署流程。

## 目录结构

```
项目根目录/
├── resources/              # 前端源码
│   ├── main.tsx           # 入口文件
│   └── ...
├── dist/                   # Vite 打包输出（生产环境）
│   ├── assets/            # JS/CSS 文件（带 hash）
│   │   ├── main-sYGtbus5.js
│   │   ├── main-xyz789.css
│   │   └── ...
│   └── .vite/
│       └── manifest.json  # 文件映射清单
├── templates/
│   └── admin.html         # 后台入口 HTML 模板
└── vite.config.ts
```

## 打包流程

### 1. 执行打包命令

```bash
bun run build
# 或
npm run build
```

打包后会生成：
- `dist/assets/` - 带 hash 的 JS/CSS 文件
- `dist/.vite/manifest.json` - 文件映射清单

### 2. Manifest 文件说明

`manifest.json` 记录了源文件到打包文件的映射：

```json
{
  "resources/main.tsx": {
    "file": "assets/main-sYGtbus5.js",
    "name": "main",
    "src": "resources/main.tsx",
    "isEntry": true,
    "css": ["assets/main-abc123.css"]
  }
}
```

**文件名带 hash 的意义**：浏览器缓存控制。每次打包后文件名变化，浏览器会自动加载最新版本，无需手动清缓存。

## 后端集成

### 读取 Manifest 并生成 HTML

后端需要读取 `manifest.json`，获取打包后的文件名，然后动态生成 HTML：

```python
import json
from pathlib import Path

# 读取 manifest
manifest_path = Path("dist/.vite/manifest.json")
manifest = json.loads(manifest_path.read_text())

# 获取入口文件
entry = manifest["resources/main.tsx"]
js_file = entry["file"]  # "assets/main-sYGtbus5.js"
css_files = entry.get("css", [])  # ["assets/main-abc123.css"]

# 生成 HTML
html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LiteCMS Admin</title>
    {"".join(f'<link rel="stylesheet" href="/{css}">' for css in css_files)}
</head>
<body>
    <div id="root"></div>
    <script type="module" src="/{js_file}"></script>
</body>
</html>
"""
```

### 在 Litestar 中实现

在 `admin_enter` 控制器中集成 manifest 读取逻辑。

## Nginx 部署配置

### 静态文件配置

```nginx
server {
    listen 80;
    server_name example.com;

    # 静态资源 - Nginx 直接处理
    location /assets/ {
        alias /path/to/project/dist/assets/;
        
        # 长期缓存（文件名有 hash，可以安全缓存）
        expires 1y;
        add_header Cache-Control "public, immutable";
        
        # 开启 gzip
        gzip on;
        gzip_types application/javascript text/css;
    }

    # 其他请求 - 代理到 Litestar
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 关键点说明

| 配置 | 说明 |
|------|------|
| `alias` | 指向 `dist/assets/` 目录 |
| `expires 1y` | 缓存 1 年（因为文件名有 hash） |
| `immutable` | 告诉浏览器文件不会变 |
| `gzip` | 压缩 JS/CSS，减少传输大小 |

## 完整流程图

```
开发环境:
  bun run dev → Vite 开发服务器 → HMR 热更新

生产环境:
  bun run build
       ↓
  dist/assets/main-xxx.js + manifest.json
       ↓
  部署到服务器
       ↓
  用户访问 /admin
       ↓
  Litestar 读取 manifest → 生成 HTML（含正确的 JS 路径）
       ↓
  浏览器加载 HTML → 请求 /assets/main-xxx.js
       ↓
  Nginx 返回静态文件
```

## 常见问题

### Q: 为什么不直接硬编码 JS 文件名？

A: 因为每次打包后文件名都会变（hash 不同），硬编码需要每次手动更新。

### Q: 可以禁用 hash 吗？

A: 可以，在 `vite.config.ts` 中配置：

```typescript
build: {
  rollupOptions: {
    output: {
      entryFileNames: 'assets/main.js',
      chunkFileNames: 'assets/[name].js',
      assetFileNames: 'assets/[name].[ext]'
    }
  }
}
```

但这样会有浏览器缓存问题，更新后用户可能看不到新版本。

### Q: manifest.json 需要公开访问吗？

A: 不需要。它只在服务器端读取，不需要暴露给浏览器。
