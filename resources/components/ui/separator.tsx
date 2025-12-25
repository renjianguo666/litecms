import { splitProps, type ComponentProps } from "solid-js";
import { Separator as KSeparator } from "@kobalte/core/separator";
import { cn } from "@/lib/utils";

type SeparatorProps = ComponentProps<typeof KSeparator> & {
  orientation?: "horizontal" | "vertical";
  decorative?: boolean;
};

function Separator(props: SeparatorProps) {
  const [local, others] = splitProps(props, ["class", "orientation"]);
  const orientation = () => local.orientation ?? "horizontal";

  return (
    <KSeparator
      data-slot="separator"
      orientation={orientation()}
      class={cn(
        "bg-border shrink-0",
        orientation() === "horizontal" ? "h-px w-full" : "h-full w-px",
        local.class,
      )}
      {...others}
    />
  );
}

export { Separator };
export type { SeparatorProps };
