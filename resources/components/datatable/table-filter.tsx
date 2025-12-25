import { For, Show } from "solid-js";
import { ChevronDown, Check, X } from "lucide-solid";
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
  Checkbox,
  CheckboxLabel,
  Button,
  Input,
  Badge,
} from "@/components/ui";
import type {
  FilterConfig,
  FilterState,
  FilterValue,
  SelectFilterValue,
  SelectMultiFilterValue,
  BooleanFilterValue,
  DateFilterValue,
} from "./types";

interface TableFilterProps {
  config: FilterConfig[];
  filters: FilterState;
  onChange: (filters: FilterState) => void;
}

export default function TableFilter(props: TableFilterProps) {
  const handleChange = (name: string, value: FilterValue) => {
    props.onChange({ ...props.filters, [name]: value });
  };

  return (
    <For each={props.config}>
      {(filter) => {
        switch (filter.variant) {
          case "select":
            return (
              <SelectFilter
                label={filter.label}
                placeholder={filter.placeholder}
                options={filter.options ?? []}
                value={props.filters[filter.name] as SelectFilterValue}
                onChange={(v) => handleChange(filter.name, v)}
              />
            );
          case "multi-select":
            return (
              <MultiSelectFilter
                label={filter.label}
                placeholder={filter.placeholder}
                options={filter.options ?? []}
                value={
                  (props.filters[filter.name] as SelectMultiFilterValue) ?? []
                }
                onChange={(v) => handleChange(filter.name, v)}
              />
            );
          case "boolean":
            return (
              <BooleanFilter
                label={filter.label}
                trueText={filter.trueText}
                falseText={filter.falseText}
                value={props.filters[filter.name] as BooleanFilterValue}
                onChange={(v) => handleChange(filter.name, v)}
              />
            );
          case "date":
            return (
              <DateFilter
                label={filter.label}
                placeholder={filter.placeholder}
                value={props.filters[filter.name] as DateFilterValue}
                onChange={(v) => handleChange(filter.name, v)}
              />
            );
          default:
            return null;
        }
      }}
    </For>
  );
}

// ==================== Select Filter ====================
interface SelectFilterComponentProps {
  label: string;
  placeholder?: string;
  options: { label: string; value: string }[];
  value: SelectFilterValue;
  onChange: (value: SelectFilterValue) => void;
}

function SelectFilter(props: SelectFilterComponentProps) {
  const selectedLabel = () =>
    props.options.find((o) => o.value === props.value)?.label;

  return (
    <Popover>
      <PopoverTrigger class="inline-flex h-9 items-center justify-center gap-1.5 rounded-md border border-input bg-transparent px-3 text-sm font-medium shadow-xs transition-[color,box-shadow] outline-none hover:bg-accent hover:text-accent-foreground focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]">
        <span class="text-muted-foreground">{props.label}</span>
        <Show when={props.value !== undefined && props.value !== ""}>
          <Badge variant="secondary" class="px-1.5 py-0.5 text-xs">
            {selectedLabel()}
          </Badge>
        </Show>
        <ChevronDown class="size-4 opacity-50" />
      </PopoverTrigger>

      <PopoverContent class="min-w-[180px] p-1">
        <div class="flex flex-col">
          <For each={props.options}>
            {(option) => (
              <button
                type="button"
                class={`relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground ${
                  props.value === option.value ? "bg-accent" : ""
                }`}
                onClick={() =>
                  props.onChange(
                    props.value === option.value ? undefined : option.value,
                  )
                }
              >
                <span class="absolute left-2 flex size-3.5 items-center justify-center">
                  <Show when={props.value === option.value}>
                    <Check class="size-4" />
                  </Show>
                </span>
                <span class="pl-6">{option.label}</span>
              </button>
            )}
          </For>
          <Show when={props.value !== undefined && props.value !== ""}>
            <div class="-mx-1 my-1 h-px bg-muted" />
            <button
              type="button"
              class="relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm text-muted-foreground outline-none transition-colors hover:bg-accent hover:text-accent-foreground"
              onClick={() => props.onChange(undefined)}
            >
              <X class="mr-2 size-4" />
              <span>清除选择</span>
            </button>
          </Show>
        </div>
      </PopoverContent>
    </Popover>
  );
}

// ==================== Multi Select Filter ====================
interface MultiSelectFilterComponentProps {
  label: string;
  placeholder?: string;
  options: { label: string; value: string }[];
  value: SelectMultiFilterValue;
  onChange: (value: SelectMultiFilterValue) => void;
}

function MultiSelectFilter(props: MultiSelectFilterComponentProps) {
  const selectedSet = () => new Set(props.value ?? []);

  const toggleOption = (optionValue: string) => {
    const set = selectedSet();
    if (set.has(optionValue)) {
      set.delete(optionValue);
    } else {
      set.add(optionValue);
    }
    props.onChange(Array.from(set));
  };

  const selectedLabels = () => {
    if (!props.value || props.value.length === 0) return null;
    if (props.value.length > 2) return `${props.value.length} 项`;
    return props.options
      .filter((o) => props.value.includes(o.value))
      .map((o) => o.label)
      .join(", ");
  };

  return (
    <Popover>
      <PopoverTrigger class="inline-flex h-9 items-center justify-center gap-1.5 rounded-md border border-input bg-transparent px-3 text-sm font-medium shadow-xs transition-[color,box-shadow] outline-none hover:bg-accent hover:text-accent-foreground focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]">
        <span class="text-muted-foreground">{props.label}</span>
        <Show when={props.value && props.value.length > 0}>
          <Badge variant="secondary" class="px-1.5 py-0.5 text-xs">
            {selectedLabels()}
          </Badge>
        </Show>
        <ChevronDown class="size-4 opacity-50" />
      </PopoverTrigger>

      <PopoverContent class="min-w-[200px] p-1">
        <div class="flex flex-col">
          <For each={props.options}>
            {(option) => {
              const isSelected = () => selectedSet().has(option.value);
              return (
                <Checkbox
                  checked={isSelected()}
                  onChange={() => toggleOption(option.value)}
                  class="w-full rounded-sm py-1.5 px-2 hover:bg-accent hover:text-accent-foreground"
                >
                  <CheckboxLabel class="flex-1 cursor-pointer text-sm font-normal">
                    {option.label}
                  </CheckboxLabel>
                </Checkbox>
              );
            }}
          </For>
          <Show when={props.value && props.value.length > 0}>
            <div class="-mx-1 my-1 h-px bg-muted" />
            <button
              type="button"
              class="relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm text-muted-foreground outline-none transition-colors hover:bg-accent hover:text-accent-foreground"
              onClick={() => props.onChange([])}
            >
              <X class="mr-2 size-4" />
              <span>清除全部</span>
            </button>
          </Show>
        </div>
      </PopoverContent>
    </Popover>
  );
}

// ==================== Boolean Filter ====================
interface BooleanFilterComponentProps {
  label: string;
  trueText?: string;
  falseText?: string;
  value: BooleanFilterValue;
  onChange: (value: BooleanFilterValue) => void;
}

function BooleanFilter(props: BooleanFilterComponentProps) {
  const trueText = () => props.trueText ?? "是";
  const falseText = () => props.falseText ?? "否";

  return (
    <Popover>
      <PopoverTrigger class="inline-flex h-9 items-center justify-center gap-1.5 rounded-md border border-input bg-transparent px-3 text-sm font-medium shadow-xs transition-[color,box-shadow] outline-none hover:bg-accent hover:text-accent-foreground focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]">
        <span class="text-muted-foreground">{props.label}</span>
        <Show when={props.value !== undefined}>
          <Badge variant="secondary" class="px-1.5 py-0.5 text-xs">
            {props.value ? trueText() : falseText()}
          </Badge>
        </Show>
        <ChevronDown class="size-4 opacity-50" />
      </PopoverTrigger>

      <PopoverContent class="min-w-[140px] p-1">
        <div class="flex flex-col">
          <button
            type="button"
            class={`relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground ${
              props.value === true ? "bg-accent" : ""
            }`}
            onClick={() =>
              props.onChange(props.value === true ? undefined : true)
            }
          >
            <span class="absolute left-2 flex size-3.5 items-center justify-center">
              <Show when={props.value === true}>
                <Check class="size-4" />
              </Show>
            </span>
            <span class="pl-6">{trueText()}</span>
          </button>
          <button
            type="button"
            class={`relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground ${
              props.value === false ? "bg-accent" : ""
            }`}
            onClick={() =>
              props.onChange(props.value === false ? undefined : false)
            }
          >
            <span class="absolute left-2 flex size-3.5 items-center justify-center">
              <Show when={props.value === false}>
                <Check class="size-4" />
              </Show>
            </span>
            <span class="pl-6">{falseText()}</span>
          </button>
          <Show when={props.value !== undefined}>
            <div class="-mx-1 my-1 h-px bg-muted" />
            <button
              type="button"
              class="relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm text-muted-foreground outline-none transition-colors hover:bg-accent hover:text-accent-foreground"
              onClick={() => props.onChange(undefined)}
            >
              <X class="mr-2 size-4" />
              <span>清除</span>
            </button>
          </Show>
        </div>
      </PopoverContent>
    </Popover>
  );
}

// ==================== Date Filter ====================
interface DateFilterComponentProps {
  label: string;
  placeholder?: string;
  value: DateFilterValue;
  onChange: (value: DateFilterValue) => void;
}

function DateFilter(props: DateFilterComponentProps) {
  return (
    <Popover>
      <PopoverTrigger class="inline-flex h-9 items-center justify-center gap-1.5 rounded-md border border-input bg-transparent px-3 text-sm font-medium shadow-xs transition-[color,box-shadow] outline-none hover:bg-accent hover:text-accent-foreground focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]">
        <span class="text-muted-foreground">{props.label}</span>
        <Show when={props.value}>
          <Badge variant="secondary" class="px-1.5 py-0.5 text-xs">
            {props.value}
          </Badge>
        </Show>
        <ChevronDown class="size-4 opacity-50" />
      </PopoverTrigger>

      <PopoverContent class="p-3">
        <div class="flex flex-col gap-2">
          <Input
            type="date"
            value={props.value ?? ""}
            onInput={(e) => props.onChange(e.currentTarget.value || undefined)}
          />
          <Show when={props.value}>
            <Button
              variant="ghost"
              size="sm"
              class="w-full"
              onClick={() => props.onChange(undefined)}
            >
              <X class="mr-2 size-4" />
              清除
            </Button>
          </Show>
        </div>
      </PopoverContent>
    </Popover>
  );
}

export { SelectFilter, MultiSelectFilter, BooleanFilter, DateFilter };
