# RichEditor 富文本编辑器

基于 Tiptap 封装的 SolidJS 富文本编辑器组件，提供简洁易用的编辑体验。

## 特性

- ✨ **轻量精简** - 只保留常用功能，无冗余
- 🎨 **统一样式** - 与项目风格统一
- 📱 **响应式** - 支持拖拽调整高度、全屏编辑
- 🔍 **查找替换** - 内置搜索面板
- 🖼️ **媒体支持** - 图片、视频、iframe 嵌入
- 🔒 **安全过滤** - XSS 防护，URL 白名单验证
- 📊 **字数统计** - 中英文智能统计
- 🧩 **模块化设计** - 清晰的目录结构，便于维护和扩展

## 基本用法

```tsx
import { RichEditor } from '@/components/editor';

function MyEditor() {
  const [content, setContent] = createSignal('');

  return (
    <RichEditor
      content={content()}
      onChange={setContent}
      placeholder="请输入内容..."
      showWordCount
    />
  );
}
```

## 组件属性

```typescript
interface EditorProps {
  /** 初始 HTML 内容 */
  content?: string;
  /** 占位符文本 */
  placeholder?: string;
  /** 是否只读模式 */
  readonly?: boolean;
  /** 内容变化回调 */
  onChange?: (html: string) => void;
  /** 编辑器类名 */
  class?: string;
  /** 编辑器最小高度 */
  minHeight?: string;
  /** 编辑器最大高度（超出后滚动） */
  maxHeight?: string;
  /** 是否显示字数统计 */
  showWordCount?: boolean;
  /** 图片上传回调，返回图片 URL */
  onImageUpload?: (file: File) => Promise<string>;
  /** 编辑器就绪回调，返回编辑器引用 */
  onReady?: (ref: EditorRef) => void;
}
```

## EditorRef 接口

通过 `onReady` 回调获取编辑器引用，可命令式控制编辑器：

```typescript
interface EditorRef {
  /** 获取 Tiptap Editor 实例 */
  getEditor: () => Editor | null;
  /** 设置内容（不触发 onChange） */
  setContent: (html: string) => void;
  /** 获取 HTML 内容 */
  getHTML: () => string;
  /** 获取纯文本内容 */
  getText: () => string;
  /** 聚焦编辑器 */
  focus: () => void;
  /** 清空内容 */
  clear: () => void;
}
```

### 使用示例

```tsx
let editorRef: EditorRef | undefined;

<RichEditor
  onReady={(ref) => { editorRef = ref; }}
  onChange={(html) => console.log(html)}
/>

// 命令式操作
editorRef?.setContent('<p>新内容</p>');
editorRef?.focus();
editorRef?.clear();
```

## 工具栏功能

| 功能 | 说明 | 快捷键 |
|------|------|--------|
| 撤销/重做 | 历史操作 | Ctrl+Z / Ctrl+Y |
| 查找替换 | 搜索面板 | Ctrl+F |
| 加粗 | 文字加粗 | Ctrl+B |
| 斜体 | 文字斜体 | Ctrl+I |
| 下划线 | 文字下划线 | Ctrl+U |
| 删除线 | 文字删除线 | - |
| 文字颜色 | 11 种颜色 | - |
| 背景高亮 | 9 种颜色 | - |
| 对齐方式 | 左/中/右/两端 | - |
| 插入链接 | 超链接 | - |
| 插入图片 | URL 或上传 | - |
| 插入视频 | URL 或嵌入 | - |
| 一键排版 | 自动添加首行缩进 | - |
| 源代码 | HTML 编辑 | - |
| 全屏 | 全屏编辑 | - |

## 图片上传

```tsx
<RichEditor
  onImageUpload={async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch('/api/upload', { method: 'POST', body: formData });
    const { url } = await res.json();
    return url;
  }}
/>
```

## 样式定制

编辑器使用 `styles.css` 定义 ProseMirror 内部元素样式：

- 链接样式：蓝色虚线下划线
- 图片/视频：响应式最大宽度
- iframe：16:9 比例容器
- 高亮标记：圆角背景

## 目录结构

```
editor/
├── index.tsx              # 主组件入口 + 统一导出
├── types.ts               # 类型定义
├── constants.ts           # 常量配置（颜色、默认值）
├── styles.css             # ProseMirror 样式
├── error.tsx              # 错误边界组件
│
├── core/                  # 核心扩展
│   ├── index.ts           # 模块入口
│   ├── extensions.ts      # Tiptap 扩展配置
│   ├── video-node.ts      # Video 节点扩展
│   └── iframe-node.ts     # Iframe 节点扩展
│
├── toolbar/               # 工具栏组件
│   ├── index.ts           # 模块入口
│   ├── menu-bar.tsx       # 菜单栏主组件（整合工具栏+对话框）
│   ├── button.tsx         # 通用按钮组件
│   ├── history-group.tsx  # 撤销/重做
│   ├── format-group.tsx   # 格式化（加粗、斜体等）
│   ├── color-group.tsx    # 颜色选择
│   ├── align-group.tsx    # 对齐按钮
│   ├── media-group.tsx    # 媒体插入（链接、图片、视频）
│   ├── tools-group.tsx    # 工具组（一键排版、源码、全屏）
│   └── search-group.tsx   # 搜索按钮
│
├── dialogs/               # 对话框组件
│   ├── index.ts           # 模块入口
│   ├── link-dialog.tsx    # 链接对话框
│   ├── image-dialog.tsx   # 图片对话框
│   ├── video-dialog.tsx   # 视频对话框
│   └── source-dialog.tsx  # 源代码对话框
│
├── panels/                # 面板组件
│   ├── index.ts           # 模块入口
│   ├── search-panel.tsx   # 查找替换面板
│   └── status-bar.tsx     # 状态栏（字数统计）
│
├── hooks/                 # Hooks
│   ├── index.ts           # 模块入口
│   └── use-editor-update.ts  # 编辑器状态更新 Hook
│
└── utils/                 # 工具函数
    ├── index.ts           # 模块入口
    ├── format.ts          # HTML 格式化
    ├── security.ts        # URL 安全过滤
    └── styles.ts          # 共享样式常量
```

## API 导出

```typescript
// 主组件
export { RichEditor } from './index';
export default RichEditor;

// 类型
export type { EditorProps, EditorRef, DialogType, VideoType } from './types';

// 核心扩展
export { getDefaultExtensions, Video, Iframe } from './core';

// 工具栏组件
export {
  ToolbarButton,
  ToolbarDivider,
  ToolbarGroup,
  HistoryGroup,
  FormatGroup,
  ColorGroup,
  AlignGroup,
  MediaGroup,
  ToolsGroup,
  SearchGroup,
  MenuBar,
} from './toolbar';

// 对话框组件
export { LinkDialog, ImageDialog, VideoDialog, SourceDialog } from './dialogs';

// 面板组件
export { SearchPanel, StatusBar } from './panels';

// Hooks
export { useEditorUpdate } from './hooks';

// 工具函数
export {
  formatHtmlContent,
  cleanEditorHtml,
  cleanAttributes,
  addParagraphIndent,
  validateAndSanitizeUrl,
  convertToEmbedUrl,
  isValidEmbedUrl,
  isValidHttpUrl,
  sanitizeMediaUrl,
} from './utils';
```

## 自定义工具栏

可以使用导出的工具栏组件自定义工具栏布局：

```tsx
import { ToolbarButton, HistoryGroup, FormatGroup } from '@/components/editor';
import { Bold } from 'lucide-solid';

function CustomToolbar(props: { editor: Editor }) {
  return (
    <div class="flex items-center gap-1 p-1 border-b">
      <HistoryGroup editor={props.editor} />
      <FormatGroup editor={props.editor} />
      <ToolbarButton
        onClick={() => props.editor.chain().focus().toggleBold().run()}
        isActive={props.editor.isActive('bold')}
        title="加粗"
      >
        <Bold class="w-4 h-4" />
      </ToolbarButton>
    </div>
  );
}
```

## 注意事项

1. **非受控模式** - 初始内容通过 `content` 传入，后续变化通过 `onChange` 输出，不会响应 `content` 属性变化（保留撤销/重做历史）
2. **外部重置** - 需要重置内容时，使用 `EditorRef.setContent()` 方法
3. **表单集成** - 配合 `wtform/EditorField` 使用时，自动处理表单重置
4. **模块导入** - 推荐从主入口 `@/components/editor` 导入，避免直接导入子模块