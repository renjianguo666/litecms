import { splitProps, type ComponentProps } from "solid-js";
import { Tooltip as KTooltip } from "@kobalte/core/tooltip";
import { cn } from "@/lib/utils";

const Tooltip = KTooltip;
const TooltipTrigger = KTooltip.Trigger;
const TooltipPortal = KTooltip.Portal;
const TooltipArrow = KTooltip.Arrow;

type TooltipContentProps = ComponentProps<typeof KTooltip.Content>;

function TooltipContent(props: TooltipContentProps) {
  const [local, others] = splitProps(props, ["class", "children"]);

  return (
    <KTooltip.Portal>
      <KTooltip.Content
        data-slot="tooltip-content"
        class={cn(
          "bg-primary text-primary-foreground z-50 w-fit origin-[--kb-tooltip-content-transform-origin] rounded-md px-3 py-1.5 text-xs text-balance",
          "animate-in fade-in-0 zoom-in-95",
          "data-closed:animate-out data-closed:fade-out-0 data-closed:zoom-out-95",
          "data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
          local.class,
        )}
        {...others}
      >
        {local.children}
        <KTooltip.Arrow class="fill-primary" />
      </KTooltip.Content>
    </KTooltip.Portal>
  );
}

export { Tooltip, TooltipTrigger, TooltipPortal, TooltipArrow, TooltipContent };
export type { TooltipContentProps };
