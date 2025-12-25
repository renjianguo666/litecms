import { splitProps, type ComponentProps, type JSX } from "solid-js";
import { DropdownMenu as KDropdownMenu } from "@kobalte/core/dropdown-menu";
import { Check, ChevronRight, Circle } from "lucide-solid";
import { cn } from "@/lib/utils";

const DropdownMenu = KDropdownMenu;
const DropdownMenuTrigger = KDropdownMenu.Trigger;
const DropdownMenuPortal = KDropdownMenu.Portal;
const DropdownMenuSub = KDropdownMenu.Sub;
const DropdownMenuGroup = KDropdownMenu.Group;
const DropdownMenuRadioGroup = KDropdownMenu.RadioGroup;

type DropdownMenuContentProps = ComponentProps<typeof KDropdownMenu.Content>;

function DropdownMenuContent(props: DropdownMenuContentProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KDropdownMenu.Portal>
      <KDropdownMenu.Content
        data-slot="dropdown-menu-content"
        class={cn(
          "bg-popover text-popover-foreground z-50 min-w-32 overflow-hidden rounded-md border p-1 shadow-md",
          "data-expanded:animate-in data-closed:animate-out data-closed:fade-out-0 data-expanded:fade-in-0 data-closed:zoom-out-95 data-expanded:zoom-in-95",
          "data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
          local.class,
        )}
        {...others}
      />
    </KDropdownMenu.Portal>
  );
}

type DropdownMenuItemProps = ComponentProps<typeof KDropdownMenu.Item> & {
  inset?: boolean;
  variant?: "default" | "destructive";
};

function DropdownMenuItem(props: DropdownMenuItemProps) {
  const [local, others] = splitProps(props, ["class", "inset", "variant"]);

  return (
    <KDropdownMenu.Item
      data-slot="dropdown-menu-item"
      data-inset={local.inset}
      data-variant={local.variant ?? "default"}
      class={cn(
        "relative flex cursor-default items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none select-none",
        "focus:bg-accent focus:text-accent-foreground",
        "[&_svg:not([class*='text-'])]:text-muted-foreground",
        "data-[variant=destructive]:text-destructive data-[variant=destructive]:focus:bg-destructive/10 dark:data-[variant=destructive]:focus:bg-destructive/20 data-[variant=destructive]:focus:text-destructive",
        "data-disabled:pointer-events-none data-disabled:opacity-50",
        "data-[inset=true]:pl-8",
        "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        local.class,
      )}
      {...others}
    />
  );
}

type DropdownMenuCheckboxItemProps = ComponentProps<
  typeof KDropdownMenu.CheckboxItem
>;

function DropdownMenuCheckboxItem(props: DropdownMenuCheckboxItemProps) {
  const [local, others] = splitProps(props, ["class", "children"]);

  return (
    <KDropdownMenu.CheckboxItem
      data-slot="dropdown-menu-checkbox-item"
      class={cn(
        "relative flex cursor-default items-center gap-2 rounded-sm py-1.5 pr-2 pl-8 text-sm outline-none select-none",
        "focus:bg-accent focus:text-accent-foreground",
        "data-disabled:pointer-events-none data-disabled:opacity-50",
        "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        local.class,
      )}
      {...others}
    >
      <span class="pointer-events-none absolute left-2 flex size-3.5 items-center justify-center">
        <KDropdownMenu.ItemIndicator>
          <Check class="size-4" />
        </KDropdownMenu.ItemIndicator>
      </span>
      {local.children}
    </KDropdownMenu.CheckboxItem>
  );
}

type DropdownMenuRadioItemProps = ComponentProps<
  typeof KDropdownMenu.RadioItem
>;

function DropdownMenuRadioItem(props: DropdownMenuRadioItemProps) {
  const [local, others] = splitProps(props, ["class", "children"]);

  return (
    <KDropdownMenu.RadioItem
      data-slot="dropdown-menu-radio-item"
      class={cn(
        "relative flex cursor-default items-center gap-2 rounded-sm py-1.5 pr-2 pl-8 text-sm outline-none select-none",
        "focus:bg-accent focus:text-accent-foreground",
        "data-disabled:pointer-events-none data-disabled:opacity-50",
        "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        local.class,
      )}
      {...others}
    >
      <span class="pointer-events-none absolute left-2 flex size-3.5 items-center justify-center">
        <KDropdownMenu.ItemIndicator>
          <Circle class="size-2 fill-current" />
        </KDropdownMenu.ItemIndicator>
      </span>
      {local.children}
    </KDropdownMenu.RadioItem>
  );
}

type DropdownMenuLabelProps = ComponentProps<
  typeof KDropdownMenu.GroupLabel
> & {
  inset?: boolean;
};

function DropdownMenuLabel(props: DropdownMenuLabelProps) {
  const [local, others] = splitProps(props, ["class", "inset"]);

  return (
    <KDropdownMenu.GroupLabel
      data-slot="dropdown-menu-label"
      data-inset={local.inset}
      class={cn(
        "px-2 py-1.5 text-sm font-medium",
        "data-[inset=true]:pl-8",
        local.class,
      )}
      {...others}
    />
  );
}

type DropdownMenuSeparatorProps = ComponentProps<
  typeof KDropdownMenu.Separator
>;

function DropdownMenuSeparator(props: DropdownMenuSeparatorProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KDropdownMenu.Separator
      data-slot="dropdown-menu-separator"
      class={cn("bg-border -mx-1 my-1 h-px", local.class)}
      {...others}
    />
  );
}

type DropdownMenuShortcutProps = JSX.HTMLAttributes<HTMLSpanElement>;

function DropdownMenuShortcut(props: DropdownMenuShortcutProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <span
      data-slot="dropdown-menu-shortcut"
      class={cn(
        "text-muted-foreground ml-auto text-xs tracking-widest",
        local.class,
      )}
      {...others}
    />
  );
}

type DropdownMenuSubTriggerProps = ComponentProps<
  typeof KDropdownMenu.SubTrigger
> & {
  inset?: boolean;
};

function DropdownMenuSubTrigger(props: DropdownMenuSubTriggerProps) {
  const [local, others] = splitProps(props, ["class", "inset", "children"]);

  return (
    <KDropdownMenu.SubTrigger
      data-slot="dropdown-menu-sub-trigger"
      data-inset={local.inset}
      class={cn(
        "flex cursor-default items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none select-none",
        "focus:bg-accent focus:text-accent-foreground",
        "data-expanded:bg-accent data-expanded:text-accent-foreground",
        "[&_svg:not([class*='text-'])]:text-muted-foreground",
        "data-[inset=true]:pl-8",
        "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        local.class,
      )}
      {...others}
    >
      {local.children}
      <ChevronRight class="ml-auto size-4" />
    </KDropdownMenu.SubTrigger>
  );
}

type DropdownMenuSubContentProps = ComponentProps<
  typeof KDropdownMenu.SubContent
>;

function DropdownMenuSubContent(props: DropdownMenuSubContentProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KDropdownMenu.Portal>
      <KDropdownMenu.SubContent
        data-slot="dropdown-menu-sub-content"
        class={cn(
          "bg-popover text-popover-foreground z-50 min-w-32 overflow-hidden rounded-md border p-1 shadow-lg",
          "data-expanded:animate-in data-closed:animate-out data-closed:fade-out-0 data-expanded:fade-in-0 data-closed:zoom-out-95 data-expanded:zoom-in-95",
          "data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
          local.class,
        )}
        {...others}
      />
    </KDropdownMenu.Portal>
  );
}

const DropdownMenuIcon = KDropdownMenu.Icon;
const DropdownMenuArrow = KDropdownMenu.Arrow;
const DropdownMenuItemIndicator = KDropdownMenu.ItemIndicator;

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuPortal,
  DropdownMenuSub,
  DropdownMenuGroup,
  DropdownMenuRadioGroup,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuCheckboxItem,
  DropdownMenuRadioItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
  DropdownMenuIcon,
  DropdownMenuArrow,
  DropdownMenuItemIndicator,
};
export type {
  DropdownMenuContentProps,
  DropdownMenuItemProps,
  DropdownMenuCheckboxItemProps,
  DropdownMenuRadioItemProps,
  DropdownMenuLabelProps,
  DropdownMenuSeparatorProps,
  DropdownMenuShortcutProps,
  DropdownMenuSubTriggerProps,
  DropdownMenuSubContentProps,
};
