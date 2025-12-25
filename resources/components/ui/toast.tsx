import {
  splitProps,
  type ComponentProps,
  type ParentProps,
  Show,
} from "solid-js";
import { Portal } from "solid-js/web";
import { Toast as KToast, toaster } from "@kobalte/core/toast";
import { CircleCheck, CircleX, Info, TriangleAlert, X } from "lucide-solid";
import { cn } from "@/lib/utils";

/* -----------------------------------------------------------------------------
 * Toast Components
 * -------------------------------------------------------------------------- */

type ToastProps = ComponentProps<typeof KToast>;

function Toast(props: ToastProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KToast
      class={cn(
        "group pointer-events-auto relative flex w-full items-center gap-3 overflow-hidden rounded-md border bg-background p-4 pr-8 shadow-lg",
        "data-opened:animate-in data-opened:fade-in-0 data-opened:slide-in-from-top-full data-opened:sm:slide-in-from-bottom-full",
        "data-closed:animate-out data-closed:fade-out-80 data-closed:slide-out-to-right-full",
        "data-[swipe=move]:translate-x-(--kb-toast-swipe-move-x) data-[swipe=cancel]:translate-x-0",
        "data-[swipe=end]:animate-out data-[swipe=end]:slide-out-to-right-full",
        local.class,
      )}
      {...others}
    />
  );
}

type ToastTitleProps = ComponentProps<typeof KToast.Title>;

function ToastTitle(props: ToastTitleProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KToast.Title
      class={cn("text-sm font-semibold", local.class)}
      {...others}
    />
  );
}

type ToastDescriptionProps = ComponentProps<typeof KToast.Description>;

function ToastDescription(props: ToastDescriptionProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KToast.Description
      class={cn("text-sm text-muted-foreground", local.class)}
      {...others}
    />
  );
}

type ToastCloseButtonProps = ComponentProps<typeof KToast.CloseButton>;

function ToastCloseButton(props: ToastCloseButtonProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KToast.CloseButton
      class={cn(
        "absolute right-2 top-2 rounded-md p-1 text-foreground/50 opacity-0 transition-opacity",
        "hover:text-foreground focus:outline-none focus:ring-2 focus:ring-ring",
        "group-hover:opacity-100",
        local.class,
      )}
      {...others}
    >
      <X class="size-4" />
    </KToast.CloseButton>
  );
}

function ToastRegion(props: ParentProps) {
  return (
    <>
      {props.children}
      <Portal>
        <KToast.Region duration={3000}>
          <KToast.List class="fixed bottom-0 right-0 z-100 flex max-h-screen w-full flex-col-reverse gap-2 p-4 sm:flex-col md:max-w-[420px]" />
        </KToast.Region>
      </Portal>
    </>
  );
}

/* -----------------------------------------------------------------------------
 * Toast API
 * -------------------------------------------------------------------------- */

type ToastType = "success" | "error" | "info" | "warning";

const icons: Record<ToastType, typeof CircleCheck> = {
  success: CircleCheck,
  error: CircleX,
  info: Info,
  warning: TriangleAlert,
};

const iconColors: Record<ToastType, string> = {
  success: "text-green-500",
  error: "text-destructive",
  info: "text-blue-500",
  warning: "text-yellow-500",
};

function showToast(type: ToastType, description: string, title?: string) {
  const Icon = icons[type];

  return toaster.show((props) => (
    <Toast toastId={props.toastId}>
      <Icon class={cn("size-5 shrink-0", iconColors[type])} />
      <div class="grid gap-1">
        <Show when={title}>
          <ToastTitle>{title}</ToastTitle>
        </Show>
        <ToastDescription>{description}</ToastDescription>
      </div>
      <ToastCloseButton />
    </Toast>
  ));
}

export const toast = {
  success: (description: string, title?: string) =>
    showToast("success", description, title),
  error: (description: string, title?: string) =>
    showToast("error", description, title),
  info: (description: string, title?: string) =>
    showToast("info", description, title),
  warning: (description: string, title?: string) =>
    showToast("warning", description, title),
  dismiss: (id: number) => toaster.dismiss(id),
};

/* -----------------------------------------------------------------------------
 * Exports
 * -------------------------------------------------------------------------- */

export { Toast, ToastTitle, ToastDescription, ToastCloseButton, ToastRegion };
