# hui - 优化的 UI 组件库

基于 Solid.js + Kobalte + Tailwind CSS v4 的 UI 组件库，结合了 `ui` 和 `__ui` 两个目录的优点。

## 设计原则

### 1. 函数风格

使用普通函数定义组件，更符合现代 Solid.js 约定：

```tsx
function Button(props: ButtonProps) {
  const [local, others] = splitProps(props, ["class", "variant", "size"]);
  return <button {...others} />;
}
```

### 2. 类型系统

使用 `ComponentProps` 获取 Kobalte 原生类型，保持类型安全：

```tsx
type DialogContentProps = ComponentProps<typeof KDialog.Content> & {
  showCloseButton?: boolean;
};
```

### 3. 图标方案

使用 `lucide-solid` 图标库，代码更简洁：

```tsx
import { X, Check, ChevronDown } from "lucide-solid";
```

### 4. 子组件暴露

导出所有 Kobalte 子组件，提供最大灵活性：

```tsx
export {
  Checkbox,
  CheckboxInput,
  CheckboxControl,
  CheckboxIndicator,
  CheckboxLabel,
  CheckboxDescription,
  CheckboxErrorMessage,
};
```

### 5. Tailwind CSS v4

使用简洁的 data 属性语法：

```tsx
// ✅ 推荐 (v4 语法)
"data-checked:bg-primary data-disabled:opacity-50"

// ❌ 避免 (旧语法)
"data-[checked]:bg-primary data-[disabled]:opacity-50"
```

### 6. data-slot 属性

所有组件使用 `data-slot` 属性标识，便于样式覆盖和测试：

```tsx
<div data-slot="card-header" class={cn(...)} />
```

## 组件列表

### 基础组件

| 组件 | 描述 |
|------|------|
| `Alert` | 警告提示 |
| `Badge` | 徽章标签 |
| `Button` | 按钮 |
| `Card` | 卡片容器 |
| `Input` | 输入框 |
| `Label` | 标签 |
| `Separator` | 分隔线 |
| `Skeleton` | 骨架屏 |
| `Table` | 表格 |
| `Textarea` | 多行文本框 |

### Kobalte 组件

| 组件 | 描述 |
|------|------|
| `Checkbox` | 复选框 |
| `Dialog` | 对话框 |
| `DropdownMenu` | 下拉菜单 |
| `Popover` | 弹出框 |
| `RadioGroup` | 单选框组 |
| `Select` | 选择器 |
| `Sheet` | 侧边抽屉 |
| `Switch` | 开关 |
| `Tabs` | 标签页 |
| `Toggle` | 切换按钮 |
| `Tooltip` | 工具提示 |

## 使用方法

```tsx
import {
  Button,
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/hui";

function MyComponent() {
  return (
    <Dialog>
      <DialogTrigger as={Button}>打开对话框</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>标题</DialogTitle>
          <DialogDescription>描述内容</DialogDescription>
        </DialogHeader>
        {/* 内容 */}
      </DialogContent>
    </Dialog>
  );
}
```

## 与原组件库对比

| 特性 | ui | __ui | hui (最终) |
|------|-----|------|------------|
| 函数风格 | 箭头函数 | 普通函数 | ✅ 普通函数 |
| 类型推导 | ComponentProps | 手动 interface | ✅ ComponentProps |
| 图标 | 内联 SVG | lucide-solid | ✅ lucide-solid |
| 导出方式 | 详细 | export * | ✅ export * |
| 子组件 | 全部暴露 | 部分暴露 | ✅ 全部暴露 |
| 动画语法 | data-[xxx] | 混合 | ✅ data-xxx (v4) |

## 依赖

- `solid-js`
- `@kobalte/core`
- `class-variance-authority`
- `lucide-solid`
- `tailwindcss` (v4)