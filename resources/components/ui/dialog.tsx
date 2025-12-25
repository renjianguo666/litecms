import { splitProps, type ComponentProps, type JSX, Show } from "solid-js";
import { Dialog as KDialog } from "@kobalte/core/dialog";
import { X } from "lucide-solid";
import { cn } from "@/lib/utils";

const Dialog = KDialog;
const DialogTrigger = KDialog.Trigger;
const DialogPortal = KDialog.Portal;
const DialogClose = KDialog.CloseButton;

type DialogOverlayProps = ComponentProps<typeof KDialog.Overlay>;

function DialogOverlay(props: DialogOverlayProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KDialog.Overlay
      data-slot="dialog-overlay"
      class={cn(
        "fixed inset-0 z-50 bg-black/50",
        "data-expanded:animate-in data-closed:animate-out data-closed:fade-out-0 data-expanded:fade-in-0",
        local.class,
      )}
      {...others}
    />
  );
}

type DialogContentProps = ComponentProps<typeof KDialog.Content> & {
  showCloseButton?: boolean;
};

function DialogContent(props: DialogContentProps) {
  const [local, others] = splitProps(props, [
    "class",
    "children",
    "showCloseButton",
  ]);

  const showClose = () => local.showCloseButton ?? true;

  return (
    <DialogPortal>
      <DialogOverlay />
      <KDialog.Content
        data-slot="dialog-content"
        class={cn(
          "bg-background fixed top-[50%] left-[50%] z-50 grid w-full max-w-[calc(100%-2rem)] translate-x-[-50%] translate-y-[-50%] gap-4 rounded-lg border p-6 shadow-lg duration-200 sm:max-w-lg",
          "data-expanded:animate-in data-closed:animate-out data-closed:fade-out-0 data-expanded:fade-in-0 data-closed:zoom-out-95 data-expanded:zoom-in-95",
          local.class,
        )}
        {...others}
      >
        {local.children}
        <Show when={showClose()}>
          <KDialog.CloseButton
            data-slot="dialog-close"
            class={cn(
              "absolute top-4 right-4 rounded-sm opacity-70 transition-opacity hover:opacity-100",
              "ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
              "disabled:pointer-events-none",
              "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
            )}
          >
            <X class="size-4" />
            <span class="sr-only">Close</span>
          </KDialog.CloseButton>
        </Show>
      </KDialog.Content>
    </DialogPortal>
  );
}

type DialogHeaderProps = JSX.HTMLAttributes<HTMLDivElement>;

function DialogHeader(props: DialogHeaderProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <div
      data-slot="dialog-header"
      class={cn("flex flex-col gap-2 text-center sm:text-left", local.class)}
      {...others}
    />
  );
}

type DialogFooterProps = JSX.HTMLAttributes<HTMLDivElement>;

function DialogFooter(props: DialogFooterProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <div
      data-slot="dialog-footer"
      class={cn(
        "flex flex-col-reverse gap-2 sm:flex-row sm:justify-end",
        local.class,
      )}
      {...others}
    />
  );
}

type DialogTitleProps = ComponentProps<typeof KDialog.Title>;

function DialogTitle(props: DialogTitleProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KDialog.Title
      data-slot="dialog-title"
      class={cn("text-lg leading-none font-semibold", local.class)}
      {...others}
    />
  );
}

type DialogDescriptionProps = ComponentProps<typeof KDialog.Description>;

function DialogDescription(props: DialogDescriptionProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KDialog.Description
      data-slot="dialog-description"
      class={cn("text-muted-foreground text-sm", local.class)}
      {...others}
    />
  );
}

export {
  Dialog,
  DialogTrigger,
  DialogPortal,
  DialogClose,
  DialogOverlay,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
};
export type {
  DialogOverlayProps,
  DialogContentProps,
  DialogHeaderProps,
  DialogFooterProps,
  DialogTitleProps,
  DialogDescriptionProps,
};
