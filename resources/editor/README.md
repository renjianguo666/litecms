# LitecmsEditor

基于 Tiptap v3 的富文本编辑器，纯原生 JS 实现，打包后供 Litestar/Jinja2 服务端渲染页面使用。

## 特性

- **基础格式**:加粗 / 斜体 / 删除线 / 下划线 / 撤销重做
- **段落对齐**:左 / 居中 / 右 / 两端对齐
- **链接**:插入 / 编辑 / 移除，自动识别选中文本
- **图片**:本地上传 + 远程 URL，支持拖拽上传，可拖拽调整大小
- **视频**:B 站 / 腾讯 / 优酷 / 西瓜 / YouTube / Vimeo 链接自动转 embed，支持 iframe 嵌入代码粘贴，支持视频文件 URL
- **查找替换**:可拖拽浮动面板，支持上一个 / 下一个 / 替换 / 替换全部
- **一键排版**:参考 seoserp.cn / ueditor，清空段 + 属性白名单清理 + 段落首行缩进 + 图片居中 + 图注识别
- **源代码**:直接编辑 HTML
- **全屏**:ESC 退出
- **字数统计**:支持字符上限提示
- **剪贴板图片转存**(知乎/百家号模式):粘贴 HTML 含外链 `<img>` 时立即插入内容，后台异步转存到本站；粘贴/拖拽图片文件直接上传；转存失败显示占位图提示重新上传
- **CSRF**:全局 fetch 拦截器，自动给非安全方法注入 X-CSRFToken
- **自动销毁**:HTMX swap 移除编辑器根节点时自动清理监听，避免内存泄漏

## 目录结构

```
resources/
├── app.js                     # 全局 Alpine 组件入口（app.bundle.js，所有页面加载）
├── editor.js                  # 编辑器应用层入口（editor.bundle.js，仅表单页加载）
└── editor/                    # 编辑器纯库目录
    ├── index.js               # createEditor() 工厂函数（核心）
    ├── toolbar.js             # 工具栏构建 + 命令映射表
    ├── editor.css             # 编辑器样式（与 app.css 分离独立打包）
    ├── core/
    │   ├── extensions.js      # Tiptap 扩展配置汇总（buildExtensions）
    │   ├── clipboard-image.js # 剪贴板图片转存扩展（粘贴/拖拽 + 外链异步转存）
    │   ├── video-node.js      # 自定义视频节点（视频文件）
    │   └── iframe-node.js     # 自定义 iframe 节点（嵌入视频）
    ├── dialogs/
    │   ├── modal.js           # 共享 modal 容器（所有 dialog 复用）
    │   ├── image.js           # 图片对话框（本地上传 + 远程 URL）
    │   ├── link.js            # 链接对话框
    │   ├── video.js           # 视频对话框（embed + 文件）
    │   └── source.js          # 源代码对话框
    ├── panels/
    │   └── search.js          # 查找替换浮动面板
    └── utils/
        ├── dom.js             # el() / parseTemplate() DOM 辅助函数
        ├── csrf.js            # 全局 CSRF fetch 拦截器
        ├── format.js          # 一键排版 formatHtmlContent() + 输出清理 cleanEditorHtml()
        ├── security.js        # URL 校验 / embed 转换 / 协议归一化
        ├── toast.js           # 轻量 toast 提示
        └── upload.js          # 图片上传共享工具（uploadFile / uploadRemote）
```

## 开发

### 环境要求

- Node.js 18+
- npm（包管理与构建，配合 esbuild）

### 安装依赖

```sh
npm install
```

### 开发模式(watch)

```sh
npm run dev:editor:js    # esbuild --watch，监听 editor 源码改动
npm run dev:editor:css   # tailwindcss --watch，监听 editor.css
# 或一起跑:
npm run dev:editor       # 同时监听 js + css
# 全栈（app.css + app.js + editor）一起:
npm run dev
```

监听模式下源码改动自动重新打包到 `application/static/`，浏览器刷新即可看到变化。

### 生产构建

```sh
npm run build:editor:js    # esbuild --minify，无 sourcemap
npm run build:editor:css   # tailwindcss --minify
# 或一起:
npm run build:editor
# 全栈:
npm run build
```

### 调试

- 开发模式(`dev:editor:js`)下 esbuild 开启 sourcemap，浏览器 DevTools 能直接定位到 `resources/editor/` 下的原始源文件
- 生产构建(`build:editor:js`)无 sourcemap，已压缩
- 打包格式为 ESM（`--format=esm`），通过 `<script type="module">` 加载
- 如遇"改了源码但浏览器没变化"，检查是否跑了 `dev:editor:js`，以及浏览器缓存

## 使用

### 在模板中接入（推荐方式：data-editor + data-config）

最省事的方式：textarea 加 `data-editor` 属性，配置通过 `data-config` JSON 传入，`editor.js` 会自动扫描初始化。

```html
<textarea
  name="text"
  class="hidden"
  data-editor
  data-config='{{ {"uploadUrl": url_for("media:upload"), "placeholder": "请输入内容...", "height": "300px"} | tojson }}'
>{{ form.text.data or '' }}</textarea>

<script type="module" src="{{ url_for('static', file_path='js/editor.bundle.js') }}"></script>
```

`editor.js` 自动完成：
1. 扫描所有 `[data-editor]` 元素
2. 解析 `data-config` JSON 作为 options
3. 调用 `createEditor(textarea, options)`，编辑器会自动接管为同步目标
4. 监听 `htmx:afterSwap` 事件，HTMX 局部刷新后重新扫描初始化

**说明：**
- `class="hidden"` 让 textarea 初始不可见，编辑器渲染后会替代它的视觉位置
- 编辑器内容会自动同步回 textarea（内部用 `syncTarget`），表单提交时直接拿到 `text` 字段
- 编辑器被 HTMX swap 移除时会自动销毁（`MutationObserver` 监听），无需手动调 `destroy()`

### createEditor options

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `content` | string | `""` | 初始 HTML 内容（用 textarea 接入时自动从 textarea.value 取，无需传） |
| `syncTarget` | HTMLTextAreaElement \| HTMLInputElement | `null` | 编辑器内容同步到该表单元素（textarea 接入时自动设置） |
| `inputName` | string | `""` | 未提供 `syncTarget` 时，创建该 name 的 hidden input 同步内容 |
| `placeholder` | string | `"请输入内容..."` | 空内容提示 |
| `uploadUrl` | string | `undefined` | 图片上传接口 URL |
| `skipOrigins` | string[] | `[]` | 不需要转存的域名前缀（如 OSS CDN 域名），本站 `location.origin` 自动跳过 |
| `height` | string | `"300px"` | 编辑区高度 |
| `minHeight` | string | `"100px"` | 编辑区最小高度 |
| `maxHeight` | string | `"800px"` | 编辑区最大高度 |
| `characterLimit` | number | `0` | 字符上限，0 表示不限制 |

### 返回的实例方法

| 方法 | 说明 |
|---|---|
| `getHTML()` | 获取清理后的 HTML |
| `setHTML(html)` | 设置 HTML 内容 |
| `getText()` | 获取纯文本 |
| `focus()` | 聚焦编辑器 |
| `clear()` | 清空内容 |
| `destroy()` | 销毁实例，移除 DOM 和事件监听（通常由自动销毁处理，无需手动调） |

## 后端接口约定

### 图片上传 `POST {uploadUrl}`

一个接口支持两种用法（`application/media/controllers.py` 的 `MediaController.upload`）：

| 场景 | 请求字段 | 说明 |
|------|---------|------|
| 文件上传 | `file`（UploadFile） | 粘贴/拖拽图片文件、工具栏本地上传 |
| 外链转存 | `url`（string） | 粘贴 HTML 含外链 `<img>` 时的异步转存 |

- 请求:`multipart/form-data`
- 成功响应:`{"url": "/static/uploads/202607/xxx.png"}`（200）
- 失败响应:`{"message": "错误原因"}`（400）
- CSRF:全局 fetch 拦截器自动带 `X-CSRFToken` header，后端需开启 CSRF 中间件
- URL 格式:本地存储返回 `/static/uploads/{年月}/{uuid7hex}{ext}`，OSS 返回 `{cdn_url}/{年月}/{uuid7hex}{ext}`

## 剪贴板图片转存机制

`core/clipboard-image.js` 实现知乎/百家号式的图片转存体验：

### 三种粘贴/拖拽场景

| 场景 | 行为 |
|------|------|
| 粘贴图片文件（截图等） | 上传到本站，成功插入图片；失败插入占位图 |
| 拖拽图片文件 | 同上 |
| 粘贴 HTML 含外链 `<img>` | 立即插入内容（用原始外链 src），后台异步逐张转存；成功替换 src，失败替换为占位图 |

### 转存判断规则（`shouldLocalize`）

以下 src **不转存**，直接保留：
- 相对路径（`/static/uploads/...`）-- 站内资源
- `data:` URI -- base64 内联
- `location.origin` 开头 -- 本站绝对链接
- `skipOrigins` 数组中的前缀 -- OSS CDN 域名等自有域名

其余 `http://` / `https://` 开头的绝对链接才转存。

### `skipOrigins` 配置（OSS 模式需要）

OSS 存储模式下，本站图片 URL 是 CDN 域名（如 `https://cdn.example.com/xxx.jpg`），和 `location.origin` 不同，会被误判为外站图片去转存。通过 `skipOrigins` 排除：

**自动注入链路：**
```
application/config.py 的 oss_cdn_url 配置
      ↓
settings/manager.py 的 register_template_callables 注入全局变量 media_base_url
      ↓
模板的 data-config 读取 media_base_url，是 http 开头则加入 skipOrigins
      ↓
createEditor(options.skipOrigins) -> buildExtensions -> ClipboardImage
```

**模板示例：**
```jinja2
data-config='{{ {"uploadUrl": url_for("media:upload"), "skipOrigins": [media_base_url] if media_base_url.startswith("http") else []} | tojson }}'
```

本地存储模式 `oss_cdn_url` 是 `/static/uploads`（相对路径），`skipOrigins` 为空数组，无需特殊处理。

### 转存失败占位图

转存失败时，图片 src 被替换为一个 SVG data URI 占位图（柔和灰底 + lucide 风格裂图图标 + "图片转存失败"提示文字）。

**用户处理方式**：点击选中占位图 -> 点击工具栏「插入图片」-> 上传新图 -> `setImage` 命令自动替换选中的图片节点。无需点击重传等额外交互，复用编辑器自带能力。

## 一键排版规则

调用 `formatHtmlContent(html)` 或点击工具栏「一键排版」按钮时执行:

1. **清理空段** - 删除 `<p></p>` / `<p><br></p>` / 纯空白段，保护含媒体或锚点的段
2. **拆分媒体** - 文字+图片/视频/iframe 混排段拆成独立段;多媒体同段拆成每媒体一段
3. **属性清理** - 白名单制，保留 `src/href/alt/title/width/height` 等功能性属性，删除所有 `style/class/on*/data-pm-*`
4. **图注识别** - 两级判定:
   - Tier 1:以"图1/图:/注:/Fig./Figure/图片来源/图片说明/Caption"开头 + ≤ 40 字
   - Tier 2:无引导词但 ≤ 10 字 + 无标点 + 纯文本 + 非粗体段
   - 排除伪标题(整段 `<strong>`/`<b>` 包裹)
5. **缩进/居中**:
   - 标题 `<h1>`~`<h6>`:居中
   - 纯图片段:居中
   - 图注段:居中 + `font-size: 0.875em` + `color: #6b7280`
   - 纯文本段:加两个全角空格 `　　` 首行缩进
   - 列表/引用/`<pre>` 内的段落:不动

## 安全设计

- **XSS 防护**:`cleanAttributes` 强制删除所有 `on*` 事件属性
- **URL 校验**:`security.js` 只允许 http/https 协议，拒绝 `javascript:` 等;协议相对 URL(`//host`)自动补 `https:`
- **iframe 白名单**:只允许 B 站/腾讯/优酷/西瓜/YouTube/Vimeo 的 embed URL，其他 iframe 拒绝解析
- **视频 URL 过滤**:`sanitizeVideoUrlQuery` 只保留白名单 query 参数(vid/bvid/cid/p/page 等)
- **toast 防注入**:用 `textContent` 而非 `innerHTML`
- **CSRF**:全局 fetch 拦截器，自动给 POST/PUT/PATCH/DELETE 注入 `X-CSRFToken`

## 已知限制

- 图注识别是启发式规则，无法 100% 准确。Tier 2 可能把紧跟图片的极短纯文本正文(≤ 10 字、无标点)误判为图注
- `replaceAll` 替换后选区位置不保留
- 没有表格编辑功能(只保留已有表格的属性)
- 没有协同编辑 / 多人光标
- 不支持图片裁剪 / 滤镜
- 转存失败占位图不可点击重传，需选中后用工具栏「插入图片」替换

## 技术栈

- Tiptap v3（ProseMirror 封装）
- 原生 JS（无 React/Vue/Svelte 框架依赖）
- daisyUI v5（UI 组件）
- Tailwind CSS v4（样式）
- Lucide 图标（通过 `@iconify/tailwind4`）
- esbuild（打包）
`
