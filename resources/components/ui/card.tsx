import { splitProps, type JSX } from "solid-js";
import { cn } from "@/lib/utils";

type CardProps = JSX.HTMLAttributes<HTMLDivElement>;

function Card(props: CardProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <div
      data-slot="card"
      class={cn(
        "bg-card text-card-foreground flex flex-col gap-6 rounded-xl border py-6 shadow-sm",
        local.class,
      )}
      {...others}
    />
  );
}

type CardHeaderProps = JSX.HTMLAttributes<HTMLDivElement>;

function CardHeader(props: CardHeaderProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <div
      data-slot="card-header"
      class={cn(
        "@container/card-header grid auto-rows-min grid-rows-[auto_auto] items-start gap-2 px-6 has-data-[slot=card-action]:grid-cols-[1fr_auto] [.border-b]:pb-6",
        local.class,
      )}
      {...others}
    />
  );
}

type CardTitleProps = JSX.HTMLAttributes<HTMLDivElement>;

function CardTitle(props: CardTitleProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <div
      data-slot="card-title"
      class={cn("leading-none font-semibold", local.class)}
      {...others}
    />
  );
}

type CardDescriptionProps = JSX.HTMLAttributes<HTMLDivElement>;

function CardDescription(props: CardDescriptionProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <div
      data-slot="card-description"
      class={cn("text-muted-foreground text-sm", local.class)}
      {...others}
    />
  );
}

type CardActionProps = JSX.HTMLAttributes<HTMLDivElement>;

function CardAction(props: CardActionProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <div
      data-slot="card-action"
      class={cn(
        "col-start-2 row-span-2 row-start-1 self-start justify-self-end",
        local.class,
      )}
      {...others}
    />
  );
}

type CardContentProps = JSX.HTMLAttributes<HTMLDivElement>;

function CardContent(props: CardContentProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <div
      data-slot="card-content"
      class={cn("px-6", local.class)}
      {...others}
    />
  );
}

type CardFooterProps = JSX.HTMLAttributes<HTMLDivElement>;

function CardFooter(props: CardFooterProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <div
      data-slot="card-footer"
      class={cn("flex items-center px-6 [.border-t]:pt-6", local.class)}
      {...others}
    />
  );
}

export {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardAction,
  CardContent,
  CardFooter,
};
export type {
  CardProps,
  CardHeaderProps,
  CardTitleProps,
  CardDescriptionProps,
  CardActionProps,
  CardContentProps,
  CardFooterProps,
};
