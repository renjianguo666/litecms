import {
  For,
  Show,
  createSignal,
  createMemo,
  createResource,
  type JSX,
} from "solid-js";
import {
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  createSolidTable,
  type ColumnDef,
  type PaginationState,
} from "@tanstack/solid-table";
import { Columns3, ChevronDown, Inbox, Loader2 } from "lucide-solid";

import {
  Button,
  Popover,
  PopoverTrigger,
  PopoverContent,
  Checkbox,
  CheckboxLabel,
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui";
import TablePagination from "./table-pagination";
import TableSearch from "./table-search";
import TableFilter from "./table-filter";
import type { FilterConfig, FilterState, FilterValue } from "./types";

/**
 * 查询参数类型
 */
export type TableQueryParams = {
  search?: string;
  page?: number;
  page_size?: number;
  [key: string]: FilterValue;
};

/**
 * fetcher 返回的数据结构
 */
export interface FetcherResult<TData> {
  items?: TData[];
  total?: number;
}

/**
 * fetcher 函数类型
 */
export type Fetcher<TData> = (
  params: TableQueryParams,
) => Promise<FetcherResult<TData>>;

/**
 * table.options.meta 类型，供 columns 使用
 */
export interface TableMeta {
  refetch: () => void;
}

export interface DataTableProps<TData> {
  /** 列定义 */
  columns: ColumnDef<TData>[];
  /** 数据获取函数 */
  fetcher: Fetcher<TData>;
  /** 当前查询参数（受控模式） */
  queryParams: TableQueryParams;
  /** 参数变化回调 */
  onChange?: (params: TableQueryParams) => void;
  /** 搜索框占位符 */
  searchPlaceholder?: string;
  /** 过滤器配置 */
  filterConfig?: FilterConfig[];
  /** 工具栏右侧额外内容（如添加按钮） */
  toolbarActions?: JSX.Element;
  /** 是否显示斑马纹 */
  zebra?: boolean;
  /** 是否显示列控制器 */
  showColumnToggle?: boolean;
}

export default function DataTable<TData>(props: DataTableProps<TData>) {
  // 内部数据获取
  const [result, { refetch }] = createResource(
    () => props.queryParams,
    props.fetcher,
  );

  // 从 props.queryParams 派生当前状态
  const currentSearch = () => props.queryParams.search ?? "";
  const currentPage = () => props.queryParams.page ?? 1;
  const currentPageSize = () => props.queryParams.page_size ?? 10;

  // 从 queryParams 中提取 filters（排除 search, page, page_size）
  const currentFilters = createMemo((): FilterState => {
    const { search, page, page_size, ...filters } = props.queryParams;
    return filters as FilterState;
  });

  // 列可见性状态（这个可以保持为内部状态，不需要同步到 URL）
  const [columnVisibility, setColumnVisibility] = createSignal<
    Record<string, boolean>
  >({});

  // 派生分页状态给 TanStack Table
  const paginationState = createMemo(
    (): PaginationState => ({
      pageIndex: currentPage() - 1,
      pageSize: currentPageSize(),
    }),
  );

  // 触发 onChange 的辅助函数
  const emitChange = (updates: Partial<TableQueryParams>) => {
    props.onChange?.({
      ...props.queryParams,
      ...updates,
    });
  };

  // 搜索变化处理
  const handleSearchChange = (search: string) => {
    emitChange({
      search: search || undefined,
      page: 1, // 搜索时重置到第一页
    });
  };

  // 过滤器变化处理
  const handleFilterChange = (filters: FilterState) => {
    props.onChange?.({
      search: currentSearch() || undefined,
      page: 1, // 过滤时重置到第一页
      page_size: currentPageSize(),
      ...filters,
    });
  };

  // 分页变化处理
  const handlePaginationChange = (pageIndex: number, pageSize: number) => {
    emitChange({
      page: pageIndex + 1,
      page_size: pageSize,
    });
  };

  // 重置所有查询参数
  const handleReset = () => {
    props.onChange?.({
      page: 1,
      page_size: currentPageSize(),
    });
  };

  // 创建表格实例
  const table = createSolidTable({
    get data() {
      return result()?.items ?? [];
    },
    get rowCount() {
      return result()?.total ?? 0;
    },
    columns: props.columns,
    state: {
      get pagination() {
        return paginationState();
      },
      get columnVisibility() {
        return columnVisibility();
      },
    },
    onPaginationChange: (updater) => {
      const current = paginationState();
      const next = typeof updater === "function" ? updater(current) : updater;
      handlePaginationChange(next.pageIndex, next.pageSize);
    },
    onColumnVisibilityChange: (updater) => {
      if (typeof updater === "function") {
        setColumnVisibility(updater(columnVisibility()));
      } else {
        setColumnVisibility(updater);
      }
    },
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    manualPagination: true,
    manualFiltering: true,
    manualSorting: true,
    meta: {
      refetch,
    } as TableMeta,
  });

  // 检查是否有活跃的筛选
  const hasActiveFilters = createMemo(() => {
    const filters = currentFilters();
    return (
      currentSearch() !== "" ||
      Object.keys(filters).some((k) => filters[k] !== undefined)
    );
  });

  return (
    <div class="space-y-3">
      {/* 顶部工具栏 */}
      <div class="flex flex-wrap items-center justify-between gap-3">
        {/* 左侧：搜索和筛选 */}
        <div class="flex flex-wrap items-center gap-2">
          {/* 搜索框 */}
          <TableSearch
            placeholder={props.searchPlaceholder ?? "搜索..."}
            value={currentSearch()}
            onChange={handleSearchChange}
          />

          {/* 筛选器 */}
          <TableFilter
            config={props.filterConfig ?? []}
            filters={currentFilters()}
            onChange={handleFilterChange}
          />

          {/* 重置按钮 */}
          <Show when={hasActiveFilters()}>
            <Button variant="ghost" size="sm" onClick={handleReset}>
              重置
            </Button>
          </Show>
        </div>

        {/* 右侧：列控制器和额外操作 */}
        <div class="flex items-center gap-2">
          {/* 列显示控制 */}
          <Show when={props.showColumnToggle !== false}>
            <Popover>
              <PopoverTrigger class="inline-flex h-9 items-center justify-center gap-1.5 rounded-md border border-input bg-transparent px-3 text-sm font-medium shadow-xs transition-[color,box-shadow] outline-none hover:bg-accent hover:text-accent-foreground focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]">
                <Columns3 class="size-4" />
                <span>列</span>
                <ChevronDown class="size-4 opacity-50" />
              </PopoverTrigger>

              <PopoverContent class="min-w-[200px] p-1">
                <div class="flex flex-col">
                  <For
                    each={table
                      .getAllColumns()
                      .filter((col) => col.getCanHide())}
                  >
                    {(column) => (
                      <Checkbox
                        checked={column.getIsVisible()}
                        onChange={(checked: boolean) =>
                          column.toggleVisibility(checked)
                        }
                        class="w-full rounded-sm py-1.5 px-2 hover:bg-accent hover:text-accent-foreground"
                      >
                        <CheckboxLabel class="flex-1 cursor-pointer text-sm font-normal">
                          {typeof column.columnDef.header === "string"
                            ? column.columnDef.header
                            : column.id}
                        </CheckboxLabel>
                      </Checkbox>
                    )}
                  </For>
                </div>
              </PopoverContent>
            </Popover>
          </Show>

          {/* 额外操作按钮 */}
          {props.toolbarActions}
        </div>
      </div>

      {/* 表格容器 */}
      <div class="rounded-md border">
        <Table>
          {/* 表头 */}
          <TableHeader class="bg-muted/50">
            <For each={table.getHeaderGroups()}>
              {(headerGroup) => (
                <TableRow class="hover:bg-muted/50">
                  <For each={headerGroup.headers}>
                    {(header) => (
                      <TableHead
                        class="px-3 [&:has([role=checkbox])]:pr-0 [&:has([role=checkbox])]:pl-3"
                        colSpan={header.colSpan}
                      >
                        <Show when={!header.isPlaceholder}>
                          {flexRender(
                            header.column.columnDef.header,
                            header.getContext(),
                          )}
                        </Show>
                      </TableHead>
                    )}
                  </For>
                </TableRow>
              )}
            </For>
          </TableHeader>

          {/* 表格内容 */}
          <TableBody>
            <Show
              when={!result.loading && table.getRowModel().rows.length > 0}
              fallback={
                <TableRow>
                  <TableCell
                    colSpan={table.getAllColumns().length}
                    class="h-32 text-center"
                  >
                    <Show
                      when={result.loading}
                      fallback={
                        <div class="flex flex-col items-center justify-center gap-2 py-8 text-muted-foreground">
                          <Inbox class="h-10 w-10" />
                          <p class="text-sm">没有数据</p>
                        </div>
                      }
                    >
                      <div class="flex items-center justify-center py-8">
                        <Loader2 class="h-6 w-6 animate-spin text-muted-foreground" />
                      </div>
                    </Show>
                  </TableCell>
                </TableRow>
              }
            >
              <For each={table.getRowModel().rows}>
                {(row, index) => (
                  <TableRow
                    class={
                      props.zebra !== false && index() % 2 === 1
                        ? "bg-muted/50"
                        : ""
                    }
                  >
                    <For each={row.getVisibleCells()}>
                      {(cell) => (
                        <TableCell class="px-3 py-2 [&:has([role=checkbox])]:pr-0 [&:has([role=checkbox])]:pl-3">
                          {flexRender(
                            cell.column.columnDef.cell,
                            cell.getContext(),
                          )}
                        </TableCell>
                      )}
                    </For>
                  </TableRow>
                )}
              </For>
            </Show>
          </TableBody>
        </Table>
      </div>

      {/* 底部分页 */}
      <TablePagination table={table} />
    </div>
  );
}
