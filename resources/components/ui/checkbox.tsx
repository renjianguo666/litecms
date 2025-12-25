import { splitProps, type ComponentProps, type JSX } from "solid-js";
import { Checkbox as KCheckbox } from "@kobalte/core/checkbox";
import { Check } from "lucide-solid";
import { cn } from "@/lib/utils";

type CheckboxProps = Omit<ComponentProps<typeof KCheckbox>, "children"> & {
  children?: JSX.Element;
};

function Checkbox(props: CheckboxProps) {
  const [local, others] = splitProps(props, ["class", "children"]);

  return (
    <KCheckbox
      class={cn("inline-flex items-center gap-2", local.class)}
      {...others}
    >
      <KCheckbox.Input class="peer sr-only" />
      <KCheckbox.Control
        data-slot="checkbox"
        class={cn(
          "peer size-4 shrink-0 rounded-sm border shadow-xs transition-shadow outline-none",
          "border-input dark:bg-input/30",
          "data-checked:bg-primary data-checked:text-primary-foreground data-checked:border-primary dark:data-checked:bg-primary",
          "focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]",
          "aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive",
          "disabled:cursor-not-allowed disabled:opacity-50",
        )}
      >
        <KCheckbox.Indicator
          data-slot="checkbox-indicator"
          class="grid place-content-center text-current"
        >
          <Check class="size-3.5" />
        </KCheckbox.Indicator>
      </KCheckbox.Control>
      {local.children}
    </KCheckbox>
  );
}

const CheckboxInput = KCheckbox.Input;
const CheckboxControl = KCheckbox.Control;
const CheckboxIndicator = KCheckbox.Indicator;
const CheckboxLabel = KCheckbox.Label;
const CheckboxDescription = KCheckbox.Description;
const CheckboxErrorMessage = KCheckbox.ErrorMessage;

export {
  Checkbox,
  CheckboxInput,
  CheckboxControl,
  CheckboxIndicator,
  CheckboxLabel,
  CheckboxDescription,
  CheckboxErrorMessage,
};
export type { CheckboxProps };
