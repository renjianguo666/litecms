import type { Table } from "@tanstack/solid-table";
import {
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-solid";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui";
import { Button } from "@/components/ui";
import { calculatePagination } from "./utils";

interface TablePaginationProps<TData> {
  table: Table<TData>;
}

interface PageSizeOption {
  value: string;
  label: string;
}

const pageSizeOptions: PageSizeOption[] = [
  { value: "10", label: "10" },
  { value: "20", label: "20" },
  { value: "50", label: "50" },
  { value: "100", label: "100" },
];

export default function TablePagination<TData>(
  props: TablePaginationProps<TData>,
) {
  const paginationInfo = () =>
    calculatePagination(
      props.table.getState().pagination.pageIndex + 1,
      props.table.getState().pagination.pageSize,
      props.table.getRowCount(),
    );

  const currentPageSize = () =>
    pageSizeOptions.find(
      (opt) => opt.value === String(props.table.getState().pagination.pageSize),
    );

  return (
    <div class="flex items-center justify-between px-2">
      {/* 左侧：记录信息 */}
      <div class="flex-1 text-sm text-muted-foreground">
        {paginationInfo().showingText}
      </div>

      {/* 右侧：每页条数和分页按钮 */}
      <div class="flex items-center space-x-6 lg:space-x-8">
        {/* 每页条数选择 */}
        <div class="flex items-center space-x-2">
          <p class="text-sm font-medium">每页</p>
          <Select<PageSizeOption>
            value={currentPageSize()}
            options={pageSizeOptions}
            optionValue="value"
            optionTextValue="label"
            onChange={(option) => {
              if (option) {
                props.table.setPagination({
                  pageIndex: 0,
                  pageSize: Number(option.value),
                });
              }
            }}
            itemComponent={(itemProps) => (
              <SelectItem item={itemProps.item}>
                {itemProps.item.rawValue.label}
              </SelectItem>
            )}
          >
            <SelectTrigger class="h-8 w-[70px]" size="sm">
              <SelectValue<PageSizeOption>>
                {(state) => state.selectedOption()?.label}
              </SelectValue>
            </SelectTrigger>
            <SelectContent />
          </Select>
          <p class="text-sm font-medium">条</p>
        </div>

        {/* 页码信息 */}
        <div class="flex w-[130px] items-center justify-center text-sm font-medium">
          第 {props.table.getState().pagination.pageIndex + 1} 页，共{" "}
          {props.table.getPageCount() || 1} 页
        </div>

        {/* 分页按钮 */}
        <div class="flex items-center space-x-2">
          <Button
            variant="outline"
            size="icon-sm"
            class="hidden lg:flex"
            disabled={!props.table.getCanPreviousPage()}
            onClick={() => props.table.setPageIndex(0)}
          >
            <span class="sr-only">第一页</span>
            <ChevronsLeft class="size-4" />
          </Button>
          <Button
            variant="outline"
            size="icon-sm"
            disabled={!props.table.getCanPreviousPage()}
            onClick={() => props.table.previousPage()}
          >
            <span class="sr-only">上一页</span>
            <ChevronLeft class="size-4" />
          </Button>
          <Button
            variant="outline"
            size="icon-sm"
            disabled={!props.table.getCanNextPage()}
            onClick={() => props.table.nextPage()}
          >
            <span class="sr-only">下一页</span>
            <ChevronRight class="size-4" />
          </Button>
          <Button
            variant="outline"
            size="icon-sm"
            class="hidden lg:flex"
            disabled={!props.table.getCanNextPage()}
            onClick={() =>
              props.table.setPageIndex(props.table.getPageCount() - 1)
            }
          >
            <span class="sr-only">最后一页</span>
            <ChevronsRight class="size-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
