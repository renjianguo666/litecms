import { splitProps, type ComponentProps } from "solid-js";
import { ToggleButton } from "@kobalte/core/toggle-button";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const toggleVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        default:
          "bg-transparent hover:bg-muted hover:text-muted-foreground data-[pressed]:bg-muted data-[pressed]:text-muted-foreground",
        outline:
          "border border-input bg-transparent shadow-xs hover:bg-accent hover:text-accent-foreground data-[pressed]:bg-accent data-[pressed]:text-accent-foreground",
      },
      size: {
        default: "h-9 px-3 min-w-9",
        sm: "h-8 px-2 min-w-8",
        lg: "h-10 px-4 min-w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

type ToggleProps = ComponentProps<typeof ToggleButton> &
  VariantProps<typeof toggleVariants>;

function Toggle(props: ToggleProps) {
  const [local, others] = splitProps(props, ["class", "variant", "size"]);

  return (
    <ToggleButton
      data-slot="toggle"
      class={cn(
        toggleVariants({ variant: local.variant, size: local.size }),
        local.class,
      )}
      {...others}
    />
  );
}

export { Toggle, toggleVariants };
export type { ToggleProps };
