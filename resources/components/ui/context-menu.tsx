import { splitProps, type ComponentProps } from "solid-js";
import { ContextMenu as KContextMenu } from "@kobalte/core/context-menu";
import { cn } from "@/lib/utils";

const ContextMenu = KContextMenu;
const ContextMenuTrigger = KContextMenu.Trigger;

type ContextMenuContentProps = ComponentProps<typeof KContextMenu.Content>;

function ContextMenuContent(props: ContextMenuContentProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KContextMenu.Portal>
      <KContextMenu.Content
        class={cn(
          "bg-popover text-popover-foreground z-50 min-w-32 overflow-hidden rounded-md border p-1 shadow-md",
          "animate-in fade-in-0 zoom-in-95",
          local.class,
        )}
        {...others}
      />
    </KContextMenu.Portal>
  );
}

type ContextMenuItemProps = ComponentProps<typeof KContextMenu.Item> & {
  variant?: "default" | "destructive";
};

function ContextMenuItem(props: ContextMenuItemProps) {
  const [local, others] = splitProps(props, ["class", "variant"]);

  return (
    <KContextMenu.Item
      class={cn(
        "relative flex cursor-default items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none select-none",
        "focus:bg-accent focus:text-accent-foreground",
        "data-disabled:pointer-events-none data-disabled:opacity-50",
        "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        local.variant === "destructive" &&
          "text-destructive focus:bg-destructive/10 focus:text-destructive",
        local.class,
      )}
      {...others}
    />
  );
}

type ContextMenuSeparatorProps = ComponentProps<typeof KContextMenu.Separator>;

function ContextMenuSeparator(props: ContextMenuSeparatorProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KContextMenu.Separator
      class={cn("bg-border -mx-1 my-1 h-px", local.class)}
      {...others}
    />
  );
}

export {
  ContextMenu,
  ContextMenuTrigger,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
};
