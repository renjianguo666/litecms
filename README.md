# LiteCMS

一个基于 **Litestar** (后端) 和 **SolidJS** (前端) 的轻量级内容管理系统。

## 技术栈

### 后端

- **Litestar** - 高性能 Python Web 框架
- **SQLAlchemy** + **Advanced Alchemy** - ORM 和数据库工具
- **AsyncPG** - PostgreSQL 异步驱动
- **Alembic** - 数据库迁移
- **Granian** - 高性能 ASGI 服务器

### 前端

- **SolidJS** - 响应式 UI 框架
- **TanStack Router** - 类型安全的路由
- **TanStack Table** - 表格组件
- **TanStack Form** - 表单管理
- **TailwindCSS** + **DaisyUI** - 样式框架
- **Tiptap** - 富文本编辑器
- **openapi-fetch** - 类型安全的 API 客户端

## 开发环境设置

### 前置条件

- Python >= 3.11
- Node.js (推荐使用 Bun 作为包管理器)
- PostgreSQL 数据库

### 安装依赖

```bash
# 安装 Python 依赖 (使用 uv)
uv sync

# 安装前端依赖 (使用 Bun)
bun install
```

### 启动开发服务器

```bash
# 启动后端服务
uv run dev

# 启动前端开发服务器 (另开终端)
bun run dev
```

## API Schema 工作流

本项目采用 **OpenAPI 规范** 实现前后端类型共享。后端通过 Litestar 自动生成 OpenAPI Schema，前端基于该 Schema 生成 TypeScript 类型定义和 Zod 验证模式。

### 工作流程图

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────────┐
│   Litestar      │     │   openapi.json  │     │  TypeScript Types       │
│   后端 API      │ ──▶ │   OpenAPI 规范  │ ──▶ │  (api.d.ts)             │
│   定义          │     │                 │     │  用于 openapi-fetch     │
└─────────────────┘     └─────────────────┘     └─────────────────────────┘
                                │
                                ▼
                        ┌─────────────────────────┐
                        │  Zod Schemas            │
                        │  (schemas.ts)           │
                        │  运行时验证 (Zod 4)     │
                        └─────────────────────────┘
```

### 步骤说明

#### 1. 生成 OpenAPI Schema (后端)

当后端 API 开发完成或有变更后，执行以下命令生成 OpenAPI 规范文件：

```bash
litestar schema openapi --output openapi.json
```

此命令会扫描所有 Litestar 路由定义，生成符合 OpenAPI 3.1.0 规范的 JSON 文件。

#### 2. 生成 TypeScript 类型定义

，生成供 `openapi-fetch` 使用的类型定义：

```bash
bunx openapi-typescript ./resources/openapi.json -o ./resources/openapi.d.ts
```

生成的 `api.d.ts` 包含：

- `paths` - 所有 API 端点的类型定义
- `components` - 请求/响应的 Schema 类型
- `operations` - 各操作的详细类型

#### 3. 生成 Zod Schema (使用 @hey-api/openapi-ts)

使用 [@hey-api/openapi-ts](https://github.com/hey-api/openapi-ts) 生成支持 **Zod 4** 的运行时验证 Schema：

```bash
bunx @hey-api/openapi-ts -i ./resources/openapi.json -o ./resources/openapi -p zod
```

生成的 `openapi.schemas.ts` 包含：

- 语义化命名的实体 Schema（如 `zUserSchema`, `zArticleCreateSchema`）
- API 请求数据 Schema（如 `zApiUsersListUsersData`，包含 query/path/body）
- API 响应 Schema（如 `zApiUsersListUsersResponse`）
- 原生支持 Zod 4 语法（如 `z.uuid()`, `z.iso.datetime()` 等）

### 一键执行脚本

为方便开发，可以在项目根目录创建以下脚本：

```bash
# generate-api.sh (Linux/macOS)
#!/bin/bash
litestar schema openapi --output resources/openapi.json
cd resources
bunx openapi-typescript ./openapi.json -o openapi.d.ts
bunx @hey-api/openapi-ts -i ./openapi.json -o ./generated -p zod
mv ./generated/zod.gen.ts ./openapi.schemas.ts
rm -rf ./generated
echo "API types generated successfully!"
```

```powershell
# generate-api.ps1 (Windows PowerShell)
litestar schema openapi --output resources/openapi.json
Set-Location resources
bunx openapi-typescript ./openapi.json -o openapi.d.ts
bunx @hey-api/openapi-ts -i ./openapi.json -o ./generated -p zod
Move-Item ./generated/zod.gen.ts ./openapi.schemas.ts -Force
Remove-Item ./generated -Recurse -Force
Write-Host "API types generated successfully!"
```

## 前端 API 调用示例

### 使用 openapi-fetch

```typescript
import createClient from "openapi-fetch";
import type { paths } from "./api.d.ts";

const client = createClient<paths>({ baseUrl: "/" });

// 类型安全的 API 调用
const { data, error } = await client.POST("/api/login", {
  body: {
    username: "admin",
    password: "password",
  },
});

// data 自动推断为 UserSchema 类型
if (data) {
  console.log(data.username);
}
```

### 使用 Zod Schema 验证

```typescript
import { LoginFormSchema, UserSchema } from "@/lib/api";

// 表单数据验证
const loginData = LoginFormSchema.parse({
  username: "admin",
  password: "password",
});

// API 响应验证
const user = UserSchema.parse(responseData);
```

## 项目结构

```
litecms/
├── application/           # 后端应用代码
├── migrations/            # 数据库迁移文件
├── resources/             # 前端资源
│   ├── assets/            # 静态资源
│   ├── components/        # 通用组件
│   ├── features/          # 功能模块
│   ├── lib/               # 工具库
│   ├── routes/            # 路由页面
│   ├── openapi.d.ts       # [生成] OpenAPI 类型定义 (openapi-typescript)
│   ├── openapi.json       # [生成] OpenAPI 规范
│   └── openapi.schemas.ts # [生成] Zod Schema (@hey-api/openapi-ts)
├── public/                # 公共静态文件
├── main.py                # 应用入口
├── pyproject.toml         # Python 项目配置
└── package.json           # 前端项目配置
```

## 常用命令

| 命令                                                               | 说明                 |
| ------------------------------------------------------------------ | -------------------- |
| `uv run dev`                                                       | 启动后端开发服务器   |
| `uv run serve`                                                     | 启动生产服务器       |
| `bun run dev`                                                      | 启动前端开发服务器   |
| `bun run build`                                                    | 构建前端生产版本     |
| `litestar schema openapi --output resources/openapi.json`          | 生成 OpenAPI Schema  |
| `bunx openapi-typescript ./openapi.json -o openapi.d.ts`           | 生成 TypeScript 类型 |
| `bunx @hey-api/openapi-ts -i ./openapi.json -o ./generated -p zod` | 生成 Zod Schema      |

## 相关链接

- [Litestar](https://litestar.dev/) - 后端框架
- [openapi-typescript](https://github.com/openapi-ts/openapi-typescript) - OpenAPI 转 TypeScript 类型
- [openapi-fetch](https://github.com/openapi-ts/openapi-typescript/tree/main/packages/openapi-fetch) - 类型安全的 fetch 客户端
- [@hey-api/openapi-ts](https://github.com/hey-api/openapi-ts) - OpenAPI 转 Zod Schema（支持 Zod 4）

## License

MIT
