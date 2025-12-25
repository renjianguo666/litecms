import { splitProps, type ComponentProps } from "solid-js";
import { RadioGroup as KRadioGroup } from "@kobalte/core/radio-group";
import { Circle } from "lucide-solid";
import { cn } from "@/lib/utils";

const RadioGroup = KRadioGroup;
const RadioGroupLabel = KRadioGroup.Label;
const RadioGroupDescription = KRadioGroup.Description;
const RadioGroupErrorMessage = KRadioGroup.ErrorMessage;

type RadioGroupItemProps = ComponentProps<typeof KRadioGroup.Item>;

function RadioGroupItem(props: RadioGroupItemProps) {
  const [local, others] = splitProps(props, ["class", "children"]);

  return (
    <KRadioGroup.Item
      data-slot="radio-group-item"
      class={cn("flex items-center gap-2", local.class)}
      {...others}
    >
      <KRadioGroup.ItemInput class="peer sr-only" />
      <KRadioGroup.ItemControl
        data-slot="radio-group-control"
        class={cn(
          "aspect-square size-4 shrink-0 rounded-full border shadow-xs transition-shadow outline-none",
          "border-input dark:bg-input/30",
          "peer-focus-visible:border-ring peer-focus-visible:ring-ring/50 peer-focus-visible:ring-[3px]",
          "aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive",
          "data-[checked]:border-primary data-[checked]:text-primary",
          "disabled:cursor-not-allowed disabled:opacity-50"
        )}
      >
        <KRadioGroup.ItemIndicator class="flex items-center justify-center">
          <Circle class="size-2.5 fill-current" />
        </KRadioGroup.ItemIndicator>
      </KRadioGroup.ItemControl>
      {local.children}
    </KRadioGroup.Item>
  );
}

type RadioGroupItemLabelProps = ComponentProps<typeof KRadioGroup.ItemLabel>;

function RadioGroupItemLabel(props: RadioGroupItemLabelProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <KRadioGroup.ItemLabel
      data-slot="radio-group-item-label"
      class={cn(
        "text-sm font-medium leading-none select-none cursor-pointer",
        "peer-disabled:cursor-not-allowed peer-disabled:opacity-50",
        local.class
      )}
      {...others}
    />
  );
}

const RadioGroupItemInput = KRadioGroup.ItemInput;
const RadioGroupItemControl = KRadioGroup.ItemControl;
const RadioGroupItemIndicator = KRadioGroup.ItemIndicator;

export {
  RadioGroup,
  RadioGroupLabel,
  RadioGroupDescription,
  RadioGroupErrorMessage,
  RadioGroupItem,
  RadioGroupItemLabel,
  RadioGroupItemInput,
  RadioGroupItemControl,
  RadioGroupItemIndicator,
};
export type { RadioGroupItemProps, RadioGroupItemLabelProps };
