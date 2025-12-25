# WTForm 表单组件

基于 TanStack Form (solid-form) 封装的表单组件库，提供声明式、类型安全的表单构建方式。

## 特性

- 🎯 **类型安全** - 完整的 TypeScript 支持，字段名和值类型推断
- 🔗 **便捷绑定** - `form.StringField` 语法，无需手动传递 field 对象
- 🎨 **DaisyUI 样式** - 开箱即用的美观样式
- ✅ **表单验证** - 继承 TanStack Form 强大的验证能力
- 🔄 **响应式** - 基于 SolidJS 的细粒度响应式

## 安装依赖

```bash
bun add @tanstack/solid-form
```

## 基本用法

```tsx
import { useWTForm } from '@/components/wtform';

function MyForm() {
  const form = useWTForm(() => ({
    defaultValues: {
      name: '',
      email: '',
      age: 0,
      bio: '',
      role: '',
      active: true,
      newsletter: false,
      content: '',
    },
    onSubmit: async ({ value }) => {
      console.log('提交数据:', value);
    },
  }));

  return (
    <form.Form class="space-y-4">
      <form.StringField name="name" label="姓名" placeholder="请输入姓名" />
      <form.StringField name="email" label="邮箱" type="email" />
      <form.NumberField name="age" label="年龄" min={0} max={150} />
      <form.TextareaField name="bio" label="简介" rows={4} />
      <form.SelectField
        name="role"
        label="角色"
        options={[
          { label: '管理员', value: 'admin' },
          { label: '用户', value: 'user' },
        ]}
      />
      <form.SwitchField name="active" label="是否激活" />
      <form.CheckboxField name="newsletter" label="订阅邮件" />
      <form.EditorField name="content" label="内容" showWordCount />
      
      <div class="flex gap-2">
        <form.SubmitButton>提交</form.SubmitButton>
        <form.ResetButton>重置</form.ResetButton>
      </div>
    </form.Form>
  );
}
```

## 可用字段组件

### StringField

文本输入字段。

```tsx
<form.StringField
  name="email"
  label="邮箱"
  type="email"           // 'text' | 'email' | 'password' | 'url' | 'tel'
  placeholder="请输入"
  description="用于登录"
  disabled={false}
/>
```

### NumberField

数字输入字段。

```tsx
<form.NumberField
  name="age"
  label="年龄"
  min={0}
  max={150}
  step={1}
  placeholder="请输入年龄"
/>
```

### TextareaField

多行文本字段。

```tsx
<form.TextareaField
  name="bio"
  label="简介"
  rows={4}
  placeholder="请输入简介"
/>
```

### SelectField

下拉选择字段。

```tsx
<form.SelectField
  name="role"
  label="角色"
  placeholder="请选择"
  options={[
    { label: '管理员', value: 'admin' },
    { label: '用户', value: 'user' },
  ]}
/>
```

### CheckboxField

复选框字段。

```tsx
<form.CheckboxField
  name="agree"
  label="同意服务条款"
  description="请阅读后勾选"
/>
```

### SwitchField

开关字段。

```tsx
<form.SwitchField
  name="active"
  label="启用状态"
  description="开启后生效"
/>
```

### EditorField

富文本编辑器字段（集成 RichEditor）。

```tsx
<form.EditorField
  name="content"
  label="文章内容"
  placeholder="请输入内容..."
  minHeight="200px"
  maxHeight="500px"
  showWordCount
/>
```

## 按钮组件

### SubmitButton

```tsx
<form.SubmitButton class="btn-primary">
  保存
</form.SubmitButton>
```

### ResetButton

```tsx
<form.ResetButton variant="outline">  {/* 'outline' | 'ghost' */}
  重置
</form.ResetButton>
```

## 文件结构

```
wtform/
├── index.ts          # 导出入口
├── form-hook.tsx     # useWTForm Hook 实现
├── context.ts        # 表单上下文
├── types.ts          # 类型定义
├── fields/           # 字段组件
│   ├── index.ts
│   ├── string.tsx
│   ├── number.tsx
│   ├── textarea.tsx
│   ├── select.tsx
│   ├── checkbox.tsx
│   ├── switch.tsx
│   └── editor.tsx
└── buttons/          # 按钮组件
    ├── index.ts
    ├── submit-button.tsx
    └── reset-button.tsx
```

## API 导出

```typescript
// Hook
export { useWTForm, useAppForm, withForm } from './form-hook';

// Context
export { fieldContext, formContext, useFieldContext, useFormContext } from './context';

// Types
export type {
  SelectOption,
  BaseFieldProps,
  StringFieldProps,
  NumberFieldProps,
  TextareaFieldProps,
  SelectFieldProps,
  CheckboxFieldProps,
  SwitchFieldProps,
  EditorFieldProps,
  SubmitButtonProps,
  ResetButtonProps,
} from './types';
```
