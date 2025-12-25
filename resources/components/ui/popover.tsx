import { splitProps, type ComponentProps } from "solid-js";
import { Popover as KPopover } from "@kobalte/core/popover";
import { X } from "lucide-solid";
import { cn } from "@/lib/utils";

const Popover = KPopover;
const PopoverTrigger = KPopover.Trigger;
const PopoverAnchor = KPopover.Anchor;
const PopoverPortal = KPopover.Portal;
const PopoverTitle = KPopover.Title;
const PopoverDescription = KPopover.Description;
const PopoverArrow = KPopover.Arrow;

type PopoverContentProps = ComponentProps<typeof KPopover.Content>;

function PopoverContent(props: PopoverContentProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KPopover.Portal>
      <KPopover.Content
        data-slot="popover-content"
        class={cn(
          "bg-popover text-popover-foreground z-50 w-72 rounded-md border p-4 shadow-md outline-none",
          "data-expanded:animate-in data-closed:animate-out data-closed:fade-out-0 data-expanded:fade-in-0 data-closed:zoom-out-95 data-expanded:zoom-in-95",
          "data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
          local.class,
        )}
        {...others}
      />
    </KPopover.Portal>
  );
}

type PopoverCloseButtonProps = ComponentProps<typeof KPopover.CloseButton>;

function PopoverCloseButton(props: PopoverCloseButtonProps) {
  const [local, others] = splitProps(props, ["class", "children"]);

  return (
    <KPopover.CloseButton
      data-slot="popover-close"
      class={cn(
        "absolute top-4 right-4 rounded-sm opacity-70 transition-opacity hover:opacity-100",
        "ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        "disabled:pointer-events-none",
        "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        local.class,
      )}
      {...others}
    >
      {local.children ?? <X class="size-4" />}
    </KPopover.CloseButton>
  );
}

export {
  Popover,
  PopoverTrigger,
  PopoverAnchor,
  PopoverPortal,
  PopoverTitle,
  PopoverDescription,
  PopoverArrow,
  PopoverContent,
  PopoverCloseButton,
};
export type { PopoverContentProps, PopoverCloseButtonProps };
