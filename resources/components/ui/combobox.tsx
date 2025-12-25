import { splitProps, type ComponentProps } from "solid-js";
import { Combobox as KCombobox } from "@kobalte/core/combobox";
import { Check } from "lucide-solid";
import { cn } from "@/lib/utils";

// 直接导出原始组件
const Combobox = KCombobox;
const ComboboxControl = KCombobox.Control;
const ComboboxTrigger = KCombobox.Trigger;
const ComboboxIcon = KCombobox.Icon;
const ComboboxPortal = KCombobox.Portal;
const ComboboxListbox = KCombobox.Listbox;
const ComboboxArrow = KCombobox.Arrow;
const ComboboxLabel = KCombobox.Label;
const ComboboxDescription = KCombobox.Description;
const ComboboxErrorMessage = KCombobox.ErrorMessage;
const ComboboxHiddenSelect = KCombobox.HiddenSelect;
const ComboboxSection = KCombobox.Section;
const ComboboxItemLabel = KCombobox.ItemLabel;
const ComboboxItemDescription = KCombobox.ItemDescription;
const ComboboxItemIndicator = KCombobox.ItemIndicator;

// 带样式的输入框
type ComboboxInputProps = ComponentProps<typeof KCombobox.Input>;

function ComboboxInput(props: ComboboxInputProps) {
  const [local, others] = splitProps(props, ["class"]);
  return (
    <KCombobox.Input
      class={cn(
        "placeholder:text-muted-foreground flex h-10 w-full rounded-md bg-transparent py-3 text-sm outline-none disabled:cursor-not-allowed disabled:opacity-50",
        local.class,
      )}
      {...others}
    />
  );
}

// 带样式的内容区域
type ComboboxContentProps = ComponentProps<typeof KCombobox.Content>;

function ComboboxContent(props: ComboboxContentProps) {
  const [local, others] = splitProps(props, ["class"]);
  return (
    <KCombobox.Portal>
      <KCombobox.Content
        class={cn(
          "bg-popover text-popover-foreground z-50 min-w-32 overflow-hidden rounded-md border shadow-md",
          "data-expanded:animate-in data-closed:animate-out data-closed:fade-out-0 data-expanded:fade-in-0 data-closed:zoom-out-95 data-expanded:zoom-in-95",
          local.class,
        )}
        {...others}
      />
    </KCombobox.Portal>
  );
}

// 带样式的列表项
type ComboboxItemProps = ComponentProps<typeof KCombobox.Item>;

function ComboboxItem(props: ComboboxItemProps) {
  const [local, others] = splitProps(props, ["class", "children"]);
  return (
    <KCombobox.Item
      class={cn(
        "relative flex w-full cursor-default items-center gap-2 rounded-sm py-1.5 pr-8 pl-2 text-sm outline-none select-none",
        "data-highlighted:bg-accent data-highlighted:text-accent-foreground",
        "data-disabled:pointer-events-none data-disabled:opacity-50",
        local.class,
      )}
      {...others}
    >
      <KCombobox.ItemLabel>{local.children}</KCombobox.ItemLabel>
      <span class="absolute right-2 flex size-3.5 items-center justify-center">
        <KCombobox.ItemIndicator>
          <Check class="size-4" />
        </KCombobox.ItemIndicator>
      </span>
    </KCombobox.Item>
  );
}

export {
  Combobox,
  ComboboxControl,
  ComboboxInput,
  ComboboxTrigger,
  ComboboxIcon,
  ComboboxPortal,
  ComboboxContent,
  ComboboxListbox,
  ComboboxArrow,
  ComboboxLabel,
  ComboboxDescription,
  ComboboxErrorMessage,
  ComboboxHiddenSelect,
  ComboboxSection,
  ComboboxItem,
  ComboboxItemLabel,
  ComboboxItemDescription,
  ComboboxItemIndicator,
};
export type { ComboboxInputProps, ComboboxContentProps, ComboboxItemProps };
