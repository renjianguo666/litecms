import {
  createSignal,
  For,
  Show,
  splitProps,
  type ComponentProps,
} from "solid-js";
import { X, ChevronDown, Search } from "lucide-solid";
import { cn } from "@/lib/utils";
import { Button } from "./button";
import { Badge } from "./badge";
import { Input } from "./input";
import { Checkbox, CheckboxLabel } from "./checkbox";
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverCloseButton,
} from "./popover";

interface MultiSelectOption {
  label: string;
  value: string;
}

interface MultiSelectProps extends Omit<ComponentProps<"div">, "onChange"> {
  /** 字段名称，用于表单识别 */
  name?: string;
  /** 选项列表 */
  options: MultiSelectOption[];
  /** 当前选中的值 */
  value: string[];
  /** 值变化回调 */
  onChange: (value: string[]) => void;
  /** 占位符文本 */
  placeholder?: string;
  /** 搜索框占位符 */
  searchPlaceholder?: string;
  /** 是否禁用 */
  disabled?: boolean;
}

function MultiSelect(props: MultiSelectProps) {
  const [local, others] = splitProps(props, [
    "name",
    "options",
    "value",
    "onChange",
    "placeholder",
    "searchPlaceholder",
    "disabled",
    "class",
  ]);

  const [search, setSearch] = createSignal("");
  const [open, setOpen] = createSignal(false);

  // 过滤选项
  const filteredOptions = () => {
    const query = search().toLowerCase();
    if (!query) return local.options;
    return local.options.filter((opt) =>
      opt.label.toLowerCase().includes(query),
    );
  };

  // 已选中的选项
  const selectedOptions = () =>
    local.options.filter((opt) => local.value.includes(opt.value));

  // 切换选中
  const toggleOption = (value: string) => {
    if (local.value.includes(value)) {
      local.onChange(local.value.filter((v) => v !== value));
    } else {
      local.onChange([...local.value, value]);
    }
  };

  // 移除选中
  const removeOption = (value: string, e: MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    local.onChange(local.value.filter((v) => v !== value));
  };

  // 清空所有
  const clearAll = (e: MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    local.onChange([]);
  };

  // 关闭并清空搜索
  const handleOpenChange = (isOpen: boolean) => {
    setOpen(isOpen);
    if (!isOpen) {
      setSearch("");
    }
  };

  return (
    <Popover open={open()} onOpenChange={handleOpenChange}>
      <PopoverTrigger
        data-slot="multi-select-trigger"
        class={cn(
          "flex min-h-9 w-full items-center justify-between gap-2 rounded-md border bg-transparent px-3 py-2 text-sm shadow-xs transition-[color,box-shadow] outline-none",
          "border-input [&_svg:not([class*='text-'])]:text-muted-foreground",
          "focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]",
          "aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive",
          "dark:bg-input/30 dark:hover:bg-input/50",
          "disabled:cursor-not-allowed disabled:opacity-50",
          local.disabled && "cursor-not-allowed opacity-50",
          local.class,
        )}
        disabled={local.disabled}
        {...others}
      >
        <div class="flex flex-wrap items-center gap-1 flex-1 overflow-hidden">
          <Show
            when={selectedOptions().length > 0}
            fallback={
              <span
                data-slot="multi-select-placeholder"
                class="text-muted-foreground"
              >
                {local.placeholder ?? "请选择..."}
              </span>
            }
          >
            <For each={selectedOptions()}>
              {(opt) => (
                <Badge
                  data-slot="multi-select-badge"
                  variant="secondary"
                  class="gap-1 pr-1"
                >
                  <span class="max-w-24 truncate">{opt.label}</span>
                  <button
                    type="button"
                    class="rounded-full p-0.5 hover:bg-secondary-foreground/20 transition-colors"
                    onClick={(e) => removeOption(opt.value, e)}
                  >
                    <X class="size-3" />
                  </button>
                </Badge>
              )}
            </For>
          </Show>
        </div>

        <ChevronDown class="size-4 shrink-0 opacity-50" />
      </PopoverTrigger>

      <PopoverContent
        data-slot="multi-select-content"
        class="w-(--kb-popper-anchor-width) p-0"
      >
        {/* 搜索框 */}
        <div class="p-2 border-b">
          <div class="relative">
            <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
            <Input
              data-slot="multi-select-search"
              type="text"
              autocomplete="off"
              class="pl-8 h-8"
              placeholder={local.searchPlaceholder ?? "搜索..."}
              value={search()}
              onInput={(e) => setSearch(e.currentTarget.value)}
            />
          </div>
        </div>

        {/* 选项列表 */}
        <div data-slot="multi-select-listbox" class="max-h-60 overflow-y-auto">
          <Show
            when={filteredOptions().length > 0}
            fallback={
              <div class="py-6 text-center text-sm text-muted-foreground">
                无匹配结果
              </div>
            }
          >
            <div class="p-1">
              <For each={filteredOptions()}>
                {(opt) => {
                  const isSelected = () => local.value.includes(opt.value);
                  return (
                    <Checkbox
                      checked={isSelected()}
                      onChange={() => toggleOption(opt.value)}
                      class={cn(
                        "w-full rounded-sm py-1.5 px-2",
                        "hover:bg-accent hover:text-accent-foreground",
                        "focus:bg-accent focus:text-accent-foreground",
                      )}
                    >
                      <CheckboxLabel class="flex-1 cursor-pointer text-sm font-normal">
                        {opt.label}
                      </CheckboxLabel>
                    </Checkbox>
                  );
                }}
              </For>
            </div>
          </Show>
        </div>

        {/* 底部操作栏 */}
        <div
          data-slot="multi-select-footer"
          class="flex items-center justify-between border-t p-2"
        >
          <span class="text-xs text-muted-foreground">
            {local.value.length > 0
              ? `已选择 ${local.value.length} 项`
              : "未选择"}
          </span>
          <div class="flex gap-1">
            <Show when={local.value.length > 0}>
              <Button variant="ghost" size="sm" onClick={clearAll}>
                清空
              </Button>
            </Show>
            <PopoverCloseButton
              as={Button}
              variant="ghost"
              size="sm"
              class="static opacity-100"
            >
              完成
            </PopoverCloseButton>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}

export { MultiSelect };
export type { MultiSelectProps, MultiSelectOption };
