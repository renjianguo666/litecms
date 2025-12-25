import { Show, For } from "solid-js";
import { X, ChevronDown, Check } from "lucide-solid";
import { Combobox } from "@kobalte/core/combobox";
import { useFieldContext } from "../context";
import type { ComboboxFieldProps, ComboboxOption } from "../types";

export function ComboboxField(props: ComboboxFieldProps) {
  const field = useFieldContext<string[]>();

  const hasError = () => {
    const f = field();
    return f.state.meta.isTouched && f.state.meta.errors.length > 0;
  };

  const errorMessages = () => {
    const f = field();
    return f.state.meta.errors
      .map((e: any) => (typeof e === "string" ? e : (e?.message ?? "")))
      .join(", ");
  };

  const selectedOptions = () =>
    props.options.filter((opt) =>
      (field().state.value ?? []).includes(opt.value),
    );

  const handleChange = (values: ComboboxOption[]) => {
    field().handleChange(values.map((v) => v.value));
  };

  const removeOption = (value: string, e: MouseEvent) => {
    e.stopPropagation();
    const current = field().state.value ?? [];
    field().handleChange(current.filter((v) => v !== value));
  };

  return (
    <div class="flex flex-col gap-2 w-full">
      <Combobox<ComboboxOption>
        multiple
        options={props.options}
        optionValue="value"
        optionTextValue="label"
        optionLabel="label"
        placeholder={props.placeholder ?? "请选择..."}
        value={selectedOptions()}
        onChange={handleChange}
        disabled={props.disabled}
        itemComponent={(itemProps) => (
          <Combobox.Item
            item={itemProps.item}
            class="relative flex w-full cursor-default items-center gap-2 rounded-sm py-1.5 pr-8 pl-2 text-sm outline-none select-none data-highlighted:bg-accent data-highlighted:text-accent-foreground data-disabled:pointer-events-none data-disabled:opacity-50"
          >
            <Combobox.ItemLabel>
              {itemProps.item.rawValue.label}
            </Combobox.ItemLabel>
            <Combobox.ItemIndicator class="absolute right-2 flex size-3.5 items-center justify-center">
              <Check class="size-4" />
            </Combobox.ItemIndicator>
          </Combobox.Item>
        )}
      >
        <Show when={props.label}>
          <Combobox.Label class="text-sm font-medium leading-none">
            {props.label}
          </Combobox.Label>
        </Show>

        <Combobox.Control<ComboboxOption> aria-label={props.label}>
          {(state) => (
            <Combobox.Trigger
              class={`flex min-h-9 w-full items-center justify-between gap-2 rounded-md border bg-transparent px-3 py-2 text-sm shadow-xs border-input focus-within:border-ring focus-within:ring-ring/50 focus-within:ring-[3px] ${hasError() ? "border-destructive" : ""} ${props.disabled ? "cursor-not-allowed opacity-50" : ""}`}
            >
              <div class="flex flex-wrap items-center gap-1 flex-1">
                <Show
                  when={state.selectedOptions().length > 0}
                  fallback={
                    <span class="text-muted-foreground">
                      {props.placeholder ?? "请选择..."}
                    </span>
                  }
                >
                  <For each={state.selectedOptions()}>
                    {(option) => (
                      <span
                        class="inline-flex items-center gap-1 rounded-md bg-secondary px-2 py-0.5 text-xs font-medium"
                        onPointerDown={(e) => e.stopPropagation()}
                      >
                        <span class="max-w-24 truncate">{option.label}</span>
                        <button
                          type="button"
                          class="rounded-full p-0.5 hover:bg-secondary-foreground/20"
                          onClick={(e) => removeOption(option.value, e)}
                        >
                          <X class="size-3" />
                        </button>
                      </span>
                    )}
                  </For>
                </Show>
                <Combobox.Input
                  class="flex-1 min-w-20 bg-transparent outline-none placeholder:text-muted-foreground text-sm"
                  placeholder={
                    state.selectedOptions().length > 0
                      ? (props.searchPlaceholder ?? "搜索...")
                      : ""
                  }
                />
              </div>

              {/* 添加全选和清除按钮 */}
              <div class="flex items-center gap-1 shrink-0">
                <Show
                  when={state.selectedOptions().length < props.options.length}
                >
                  <button
                    type="button"
                    class="text-xs text-muted-foreground hover:text-foreground"
                    onPointerDown={(e) => e.stopPropagation()}
                    onClick={(e) => {
                      e.stopPropagation();
                      field().handleChange(props.options.map((o) => o.value));
                    }}
                  >
                    全选
                  </button>
                </Show>
                <Show when={state.selectedOptions().length > 0}>
                  <button
                    type="button"
                    class="text-xs text-muted-foreground hover:text-foreground"
                    onPointerDown={(e) => e.stopPropagation()}
                    onClick={(e) => {
                      e.stopPropagation();
                      state.clear();
                    }}
                  >
                    清除
                  </button>
                </Show>
              </div>

              <Combobox.Icon>
                <ChevronDown class="size-4 opacity-50" />
              </Combobox.Icon>
            </Combobox.Trigger>
          )}
        </Combobox.Control>

        <Combobox.Portal>
          <Combobox.Content class="bg-popover text-popover-foreground z-50 min-w-32 overflow-hidden rounded-md border shadow-md data-expanded:animate-in data-closed:animate-out data-closed:fade-out-0 data-expanded:fade-in-0 data-closed:zoom-out-95 data-expanded:zoom-in-95">
            <Combobox.Listbox class="max-h-72 overflow-y-auto p-1" />
          </Combobox.Content>
        </Combobox.Portal>
      </Combobox>

      <Show when={props.description && !hasError()}>
        <p class="text-sm text-muted-foreground">{props.description}</p>
      </Show>

      <Show when={hasError()}>
        <p class="text-sm text-destructive">{errorMessages()}</p>
      </Show>
    </div>
  );
}
