import { splitProps, type ComponentProps, type JSX, Show } from "solid-js";
import { Dialog as KDialog } from "@kobalte/core/dialog";
import { X } from "lucide-solid";
import { cn } from "@/lib/utils";

const Sheet = KDialog;
const SheetTrigger = KDialog.Trigger;
const SheetClose = KDialog.CloseButton;
const SheetPortal = KDialog.Portal;

type SheetOverlayProps = ComponentProps<typeof KDialog.Overlay>;

function SheetOverlay(props: SheetOverlayProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KDialog.Overlay
      data-slot="sheet-overlay"
      class={cn(
        "fixed inset-0 z-50 bg-black/50",
        "data-expanded:animate-in data-closed:animate-out data-closed:fade-out-0 data-expanded:fade-in-0",
        local.class,
      )}
      {...others}
    />
  );
}

type SheetContentProps = ComponentProps<typeof KDialog.Content> & {
  side?: "top" | "right" | "bottom" | "left";
  showCloseButton?: boolean;
};

function SheetContent(props: SheetContentProps) {
  const [local, others] = splitProps(props, [
    "class",
    "children",
    "side",
    "showCloseButton",
  ]);

  const side = () => local.side ?? "right";
  const showClose = () => local.showCloseButton ?? true;

  return (
    <SheetPortal>
      <SheetOverlay />
      <KDialog.Content
        data-slot="sheet-content"
        class={cn(
          "bg-background fixed z-50 flex flex-col gap-4 shadow-lg transition ease-in-out",
          "data-expanded:animate-in data-closed:animate-out data-closed:duration-300 data-expanded:duration-500",
          side() === "right" &&
            "data-closed:slide-out-to-right data-expanded:slide-in-from-right inset-y-0 right-0 h-full w-3/4 border-l sm:max-w-sm",
          side() === "left" &&
            "data-closed:slide-out-to-left data-expanded:slide-in-from-left inset-y-0 left-0 h-full w-3/4 border-r sm:max-w-sm",
          side() === "top" &&
            "data-closed:slide-out-to-top data-expanded:slide-in-from-top inset-x-0 top-0 h-auto border-b",
          side() === "bottom" &&
            "data-closed:slide-out-to-bottom data-expanded:slide-in-from-bottom inset-x-0 bottom-0 h-auto border-t",
          local.class,
        )}
        {...others}
      >
        {local.children}
        <Show when={showClose()}>
          <KDialog.CloseButton
            data-slot="sheet-close"
            class={cn(
              "absolute top-4 right-4 rounded-sm opacity-70 transition-opacity hover:opacity-100",
              "ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
              "disabled:pointer-events-none",
              "data-expanded:bg-secondary",
            )}
          >
            <X class="size-4" />
            <span class="sr-only">Close</span>
          </KDialog.CloseButton>
        </Show>
      </KDialog.Content>
    </SheetPortal>
  );
}

type SheetHeaderProps = JSX.HTMLAttributes<HTMLDivElement>;

function SheetHeader(props: SheetHeaderProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <div
      data-slot="sheet-header"
      class={cn("flex flex-col gap-1.5 p-4", local.class)}
      {...others}
    />
  );
}

type SheetFooterProps = JSX.HTMLAttributes<HTMLDivElement>;

function SheetFooter(props: SheetFooterProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <div
      data-slot="sheet-footer"
      class={cn("mt-auto flex flex-col gap-2 p-4", local.class)}
      {...others}
    />
  );
}

type SheetTitleProps = ComponentProps<typeof KDialog.Title>;

function SheetTitle(props: SheetTitleProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KDialog.Title
      data-slot="sheet-title"
      class={cn("text-foreground font-semibold", local.class)}
      {...others}
    />
  );
}

type SheetDescriptionProps = ComponentProps<typeof KDialog.Description>;

function SheetDescription(props: SheetDescriptionProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KDialog.Description
      data-slot="sheet-description"
      class={cn("text-muted-foreground text-sm", local.class)}
      {...others}
    />
  );
}

export {
  Sheet,
  SheetTrigger,
  SheetClose,
  SheetPortal,
  SheetOverlay,
  SheetContent,
  SheetHeader,
  SheetFooter,
  SheetTitle,
  SheetDescription,
};
export type {
  SheetOverlayProps,
  SheetContentProps,
  SheetHeaderProps,
  SheetFooterProps,
  SheetTitleProps,
  SheetDescriptionProps,
};
