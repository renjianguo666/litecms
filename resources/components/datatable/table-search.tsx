import { createSignal, createEffect } from "solid-js";
import { Search, X } from "lucide-solid";
import { Input } from "@/components/ui";

export interface TableSearchProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  debounceDelay?: number;
  class?: string;
}

export default function TableSearch(props: TableSearchProps) {
  const [localValue, setLocalValue] = createSignal(props.value);
  let debounceTimer: ReturnType<typeof setTimeout> | undefined;

  // 同步外部值
  createEffect(() => {
    setLocalValue(props.value);
  });

  const handleInput = (e: InputEvent & { currentTarget: HTMLInputElement }) => {
    const value = e.currentTarget.value;
    setLocalValue(value);

    // 清除之前的定时器
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }

    // 设置新的防抖定时器
    debounceTimer = setTimeout(() => {
      props.onChange(value);
    }, props.debounceDelay ?? 500);
  };

  const handleClear = () => {
    setLocalValue("");
    props.onChange("");
  };

  return (
    <div class={`relative ${props.class ?? ""}`}>
      <Search class="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground pointer-events-none" />
      <Input
        id="datatable-search"
        type="text"
        value={localValue()}
        onInput={handleInput}
        placeholder={props.placeholder ?? "搜索..."}
        class="w-48 pl-8 pr-8 lg:w-64"
      />
      {localValue() && (
        <button
          type="button"
          class="absolute right-2 top-1/2 -translate-y-1/2 rounded-sm p-0.5 text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          onClick={handleClear}
        >
          <X class="size-4" />
        </button>
      )}
    </div>
  );
}
