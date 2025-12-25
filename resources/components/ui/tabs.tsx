import { splitProps, type ComponentProps } from "solid-js";
import { Tabs as KTabs } from "@kobalte/core/tabs";
import { cn } from "@/lib/utils";

const Tabs = KTabs;

type TabsListProps = ComponentProps<typeof KTabs.List>;

function TabsList(props: TabsListProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KTabs.List
      data-slot="tabs-list"
      class={cn(
        "bg-muted text-muted-foreground inline-flex h-9 w-fit items-center justify-center rounded-lg p-[3px]",
        local.class,
      )}
      {...others}
    />
  );
}

type TabsTriggerProps = ComponentProps<typeof KTabs.Trigger>;

function TabsTrigger(props: TabsTriggerProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KTabs.Trigger
      data-slot="tabs-trigger"
      class={cn(
        "inline-flex h-[calc(100%-1px)] flex-1 items-center justify-center gap-1.5 rounded-md border border-transparent px-2 py-1 text-sm font-medium whitespace-nowrap transition-[color,box-shadow]",
        "text-foreground dark:text-muted-foreground",
        "data-selected:bg-background data-selected:shadow-sm",
        "dark:data-selected:text-foreground dark:data-selected:border-input dark:data-selected:bg-input/30",
        "focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:outline-ring focus-visible:ring-[3px] focus-visible:outline-1",
        "disabled:pointer-events-none disabled:opacity-50",
        "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        local.class,
      )}
      {...others}
    />
  );
}

type TabsContentProps = ComponentProps<typeof KTabs.Content>;

function TabsContent(props: TabsContentProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KTabs.Content
      data-slot="tabs-content"
      class={cn("flex-1 outline-none", local.class)}
      {...others}
    />
  );
}

const TabsIndicator = KTabs.Indicator;

export { Tabs, TabsList, TabsTrigger, TabsContent, TabsIndicator };
export type { TabsListProps, TabsTriggerProps, TabsContentProps };
