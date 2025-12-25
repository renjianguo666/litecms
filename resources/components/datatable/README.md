# DataTable 数据表格

基于 TanStack Table (solid-table) 封装的数据表格组件，支持搜索、筛选、分页、列控制等功能。

## 特性

- 🔍 **搜索筛选** - 内置搜索框和多种筛选器
- 📄 **分页支持** - 服务端分页，自定义每页条数
- 👁️ **列控制** - 动态显示/隐藏列
- 🎨 **DaisyUI 样式** - 斑马纹、hover 效果
- ⚡ **服务端模式** - 手动分页/筛选/排序
- 🔄 **响应式** - 参数变化自动回调

## 基本用法

```tsx
import DataTable, { type TableQueryParams } from '@/components/datatable';
import { createSignal } from 'solid-js';

function UserTable() {
  const [data, setData] = createSignal([]);
  const [total, setTotal] = createSignal(0);
  const [loading, setLoading] = createSignal(false);

  const columns = [
    { accessorKey: 'id', header: 'ID' },
    { accessorKey: 'name', header: '姓名' },
    { accessorKey: 'email', header: '邮箱' },
    {
      id: 'actions',
      header: '操作',
      cell: ({ row }) => (
        <button onClick={() => handleEdit(row.original)}>编辑</button>
      ),
    },
  ];

  const handleQueryChange = async (params: TableQueryParams) => {
    setLoading(true);
    const res = await fetchUsers(params);
    setData(res.data);
    setTotal(res.total);
    setLoading(false);
  };

  return (
    <DataTable
      columns={columns}
      data={data()}
      total={total()}
      loading={loading()}
      onChange={handleQueryChange}
      searchPlaceholder="搜索用户..."
    />
  );
}
```

## 组件属性

```typescript
interface DataTableProps<TData> {
  /** 列定义 */
  columns: ColumnDef<TData>[];
  /** 数据 */
  data: TData[];
  /** 数据总数（用于分页） */
  total: number;
  /** 搜索框占位符 */
  searchPlaceholder?: string;
  /** 过滤器配置 */
  filterConfig?: FilterConfig[];
  /** 当前查询参数 */
  queryParams?: TableQueryParams;
  /** 参数变化回调 */
  onChange?: (params: TableQueryParams) => void;
  /** 工具栏右侧额外内容（如添加按钮） */
  toolbarActions?: JSX.Element;
  /** 是否显示斑马纹 */
  zebra?: boolean;
  /** 是否显示列控制器 */
  showColumnToggle?: boolean;
  /** 是否加载中 */
  loading?: boolean;
}
```

## 查询参数

```typescript
type TableQueryParams = {
  search?: string;
  page?: number;
  page_size?: number;
  [key: string]: FilterValue;  // 动态筛选字段
};
```

## 筛选器配置

### 筛选器类型

```typescript
type FilterType = 'select' | 'multi-select' | 'boolean' | 'date';

interface FilterConfig {
  name: string;           // 字段名（对应查询参数）
  variant: FilterType;    // 筛选器类型
  label: string;          // 显示标签
  placeholder?: string;   // 占位符
  options?: FilterOption[]; // select/multi-select 选项
  trueText?: string;      // boolean 为真时的文字
  falseText?: string;     // boolean 为假时的文字
}
```

### 使用示例

```tsx
<DataTable
  columns={columns}
  data={data()}
  total={total()}
  filterConfig={[
    {
      name: 'status',
      variant: 'select',
      label: '状态',
      options: [
        { label: '启用', value: 'active' },
        { label: '禁用', value: 'inactive' },
      ],
    },
    {
      name: 'is_vip',
      variant: 'boolean',
      label: 'VIP',
      trueText: '是',
      falseText: '否',
    },
    {
      name: 'created_at',
      variant: 'date',
      label: '创建日期',
    },
    {
      name: 'tags',
      variant: 'multi-select',
      label: '标签',
      options: [
        { label: '重要', value: 'important' },
        { label: '紧急', value: 'urgent' },
      ],
    },
  ]}
  onChange={handleQueryChange}
/>
```

## 工具栏操作

```tsx
<DataTable
  columns={columns}
  data={data()}
  total={total()}
  toolbarActions={
    <button class="btn btn-primary btn-sm">
      <Plus class="size-4" />
      添加
    </button>
  }
/>
```

## 列定义

使用 TanStack Table 的列定义格式：

```tsx
const columns = [
  // 基础列
  { accessorKey: 'id', header: 'ID' },
  
  // 自定义渲染
  {
    accessorKey: 'status',
    header: '状态',
    cell: ({ getValue }) => (
      <span class={`badge ${getValue() === 'active' ? 'badge-success' : 'badge-error'}`}>
        {getValue() === 'active' ? '启用' : '禁用'}
      </span>
    ),
  },
  
  // 操作列
  {
    id: 'actions',
    header: '操作',
    enableHiding: false,  // 不可隐藏
    cell: ({ row }) => (
      <div class="flex gap-2">
        <button onClick={() => handleEdit(row.original)}>编辑</button>
        <button onClick={() => handleDelete(row.original.id)}>删除</button>
      </div>
    ),
  },
];
```

## 子组件

### TableSearch

搜索框组件。

```tsx
import { TableSearch } from '@/components/datatable';

<TableSearch
  placeholder="搜索..."
  value={searchValue()}
  onChange={setSearchValue}
/>
```

### TablePagination

分页组件。

```tsx
import { TablePagination } from '@/components/datatable';

<TablePagination table={table} />
```

### 筛选器组件

```tsx
import {
  SelectFilter,
  MultiSelectFilter,
  BooleanFilter,
  DateFilter,
} from '@/components/datatable';
```

## 文件结构

```
datatable/
├── index.ts            # 导出入口
├── table.tsx           # 主组件 DataTable
├── table-search.tsx    # 搜索框组件
├── table-filter.tsx    # 筛选器组件
├── table-pagination.tsx # 分页组件
├── types.ts            # 类型定义
└── utils.ts            # 工具函数
```

## API 导出

```typescript
// 组件
export { default as DataTable } from './table';
export { default as TablePagination } from './table-pagination';
export { default as TableSearch } from './table-search';
export {
  default as TableFilter,
  SelectFilter,
  MultiSelectFilter,
  BooleanFilter,
  DateFilter,
} from './table-filter';

// 类型
export type { TableQueryParams, DataTableProps } from './table';
export type { TableSearchProps } from './table-search';
export type {
  FilterConfig,
  FilterState,
  FilterValue,
  FilterType,
  FilterOption,
  BooleanFilterValue,
  BooleanFilterProps,
  SelectFilterValue,
  SelectFilterProps,
  SelectMultiFilterValue,
  SelectMultiFilterProps,
  DateFilterValue,
  DateFilterProps,
} from './types';

// 工具函数
export { calculatePagination, cn } from './utils';
```

## 注意事项

1. **服务端模式** - 表格设置为 `manualPagination`、`manualFiltering`、`manualSorting`，需要在 `onChange` 回调中请求服务端数据
2. **分页参数** - `page` 从 1 开始（API 友好），内部 `pageIndex` 从 0 开始
3. **重置筛选** - 有活跃筛选时会显示"重置"按钮，点击清空所有筛选条件
