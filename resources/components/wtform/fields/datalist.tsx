import { Show, For, createSignal, createMemo } from "solid-js";
import { useFieldContext } from "../context";
import type { DatalistFieldProps } from "../types";

export function DatalistField(props: DatalistFieldProps) {
    const field = useFieldContext<string>();
    const [inputValue, setInputValue] = createSignal("");
    const [isOpen, setIsOpen] = createSignal(false);

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

    // 过滤选项
    const filteredOptions = createMemo(() => {
        const search = inputValue().toLowerCase();
        if (!search) return props.options;
        return props.options.filter(
            (opt) =>
                opt.label.toLowerCase().includes(search) ||
                opt.value.toLowerCase().includes(search),
        );
    });

    const handleInput = (e: InputEvent) => {
        const target = e.target as HTMLInputElement;
        setInputValue(target.value);
        field().handleChange(target.value);
        setIsOpen(true);
    };

    const handleSelect = (value: string) => {
        field().handleChange(value);
        setInputValue(value);
        setIsOpen(false);
    };

    const handleFocus = () => {
        setInputValue(field().state.value || "");
        setIsOpen(true);
    };

    const handleBlur = () => {
        // 延迟关闭，让 click 事件有机会触发
        setTimeout(() => setIsOpen(false), 150);
    };

    return (
        <div class="flex flex-col gap-2 w-full relative">
            <Show when={props.label}>
                <label class="text-sm font-medium leading-none">{props.label}</label>
            </Show>

            <div class="relative">
                <input
                    type="text"
                    value={field().state.value || ""}
                    onInput={handleInput}
                    onFocus={handleFocus}
                    onBlur={handleBlur}
                    placeholder={props.placeholder}
                    disabled={props.disabled}
                    class={`flex h-9 w-full rounded-md border bg-transparent px-3 py-1 text-sm shadow-xs transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50 ${hasError() ? "border-destructive" : "border-input"}`}
                />

                <Show when={isOpen() && filteredOptions().length > 0}>
                    <div class="absolute z-50 mt-1 w-full rounded-md border bg-popover text-popover-foreground shadow-md">
                        <ul class="max-h-48 overflow-y-auto p-1">
                            <For each={filteredOptions()}>
                                {(option) => (
                                    <li
                                        class="relative flex cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-accent hover:text-accent-foreground"
                                        onMouseDown={() => handleSelect(option.value)}
                                    >
                                        <span class="flex-1">{option.label}</span>
                                        <Show when={option.value !== option.label}>
                                            <span class="text-xs text-muted-foreground ml-2">
                                                {option.value}
                                            </span>
                                        </Show>
                                    </li>
                                )}
                            </For>
                        </ul>
                    </div>
                </Show>
            </div>

            <Show when={props.description && !hasError()}>
                <p class="text-sm text-muted-foreground">{props.description}</p>
            </Show>

            <Show when={hasError()}>
                <p class="text-sm text-destructive">{errorMessages()}</p>
            </Show>
        </div>
    );
}
