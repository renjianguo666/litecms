import { splitProps, type ComponentProps, type JSX } from "solid-js";
import { Select as KSelect } from "@kobalte/core/select";
import { Check, ChevronDown } from "lucide-solid";
import { cn } from "@/lib/utils";

const Select = KSelect;
const SelectValue = KSelect.Value;
const SelectHiddenSelect = KSelect.HiddenSelect;
const SelectSection = KSelect.Section;
const SelectDescription = KSelect.Description;
const SelectErrorMessage = KSelect.ErrorMessage;
const SelectItemDescription = KSelect.ItemDescription;

type SelectTriggerProps = ComponentProps<typeof KSelect.Trigger> & {
  size?: "sm" | "default";
};

function SelectTrigger(props: SelectTriggerProps) {
  const [local, others] = splitProps(props, ["class", "size", "children"]);
  const size = () => local.size ?? "default";

  return (
    <KSelect.Trigger
      data-slot="select-trigger"
      data-size={size()}
      class={cn(
        "flex w-fit items-center justify-between gap-2 rounded-md border bg-transparent px-3 py-2 text-sm whitespace-nowrap shadow-xs transition-[color,box-shadow] outline-none",
        "border-input data-placeholder:text-muted-foreground [&_svg:not([class*='text-'])]:text-muted-foreground",
        "focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]",
        "aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive",
        "dark:bg-input/30 dark:hover:bg-input/50",
        "disabled:cursor-not-allowed disabled:opacity-50",
        "data-[size=default]:h-9 data-[size=sm]:h-8",
        "*:data-[slot=select-value]:line-clamp-1 *:data-[slot=select-value]:flex *:data-[slot=select-value]:items-center *:data-[slot=select-value]:gap-2",
        "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        local.class,
      )}
      {...others}
    >
      {local.children}
      <KSelect.Icon as={ChevronDown} class="size-4 opacity-50" />
    </KSelect.Trigger>
  );
}

type SelectContentProps = ComponentProps<typeof KSelect.Content>;

function SelectContent(props: SelectContentProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KSelect.Portal>
      <KSelect.Content
        data-slot="select-content"
        class={cn(
          "bg-popover text-popover-foreground relative z-50 min-w-32 max-h-96 overflow-hidden rounded-md border shadow-md",
          "data-expanded:animate-in data-closed:animate-out data-closed:fade-out-0 data-expanded:fade-in-0 data-closed:zoom-out-95 data-expanded:zoom-in-95",
          "data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
          local.class,
        )}
        {...others}
      >
        <KSelect.Listbox class="p-1 max-h-72 overflow-y-auto" />
      </KSelect.Content>
    </KSelect.Portal>
  );
}

type SelectItemProps = ComponentProps<typeof KSelect.Item>;

function SelectItem(props: SelectItemProps) {
  const [local, others] = splitProps(props, ["class", "children"]);

  return (
    <KSelect.Item
      data-slot="select-item"
      class={cn(
        "relative flex w-full cursor-default items-center gap-2 rounded-sm py-1.5 pr-8 pl-2 text-sm outline-none select-none",
        "focus:bg-accent focus:text-accent-foreground",
        "[&_svg:not([class*='text-'])]:text-muted-foreground",
        "data-disabled:pointer-events-none data-disabled:opacity-50",
        "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        local.class,
      )}
      {...others}
    >
      <span class="absolute right-2 flex size-3.5 items-center justify-center">
        <KSelect.ItemIndicator>
          <Check class="size-4" />
        </KSelect.ItemIndicator>
      </span>
      <KSelect.ItemLabel>{local.children}</KSelect.ItemLabel>
    </KSelect.Item>
  );
}

type SelectLabelProps = ComponentProps<typeof KSelect.Label>;

function SelectLabel(props: SelectLabelProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KSelect.Label
      data-slot="select-label"
      class={cn(
        "text-muted-foreground px-2 py-1.5 text-xs font-medium",
        local.class,
      )}
      {...others}
    />
  );
}

type SelectSeparatorProps = JSX.HTMLAttributes<HTMLHRElement>;

function SelectSeparator(props: SelectSeparatorProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <hr
      data-slot="select-separator"
      class={cn("bg-border pointer-events-none -mx-1 my-1 h-px", local.class)}
      {...others}
    />
  );
}

const SelectIcon = KSelect.Icon;
const SelectPortal = KSelect.Portal;
const SelectListbox = KSelect.Listbox;
const SelectItemIndicator = KSelect.ItemIndicator;
const SelectItemLabel = KSelect.ItemLabel;

export {
  Select,
  SelectValue,
  SelectHiddenSelect,
  SelectSection,
  SelectDescription,
  SelectErrorMessage,
  SelectItemDescription,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectIcon,
  SelectPortal,
  SelectListbox,
  SelectItemIndicator,
  SelectItemLabel,
};
export type {
  SelectTriggerProps,
  SelectContentProps,
  SelectItemProps,
  SelectLabelProps,
  SelectSeparatorProps,
};
