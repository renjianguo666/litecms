import { splitProps, type ComponentProps, type JSX } from "solid-js";
import { Switch as KSwitch } from "@kobalte/core/switch";
import { cn } from "@/lib/utils";

type SwitchProps = Omit<ComponentProps<typeof KSwitch>, "children"> & {
  children?: JSX.Element;
};

function Switch(props: SwitchProps) {
  const [local, others] = splitProps(props, ["class", "children"]);

  return (
    <KSwitch
      class={cn("inline-flex items-center gap-2", local.class)}
      {...others}
    >
      <KSwitch.Input class="peer sr-only" />
      <KSwitch.Control
        data-slot="switch"
        class={cn(
          "peer inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent shadow-xs transition-colors",
          "bg-input data-checked:bg-primary",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
          "disabled:cursor-not-allowed disabled:opacity-50",
        )}
      >
        <KSwitch.Thumb
          data-slot="switch-thumb"
          class={cn(
            "pointer-events-none block size-4 rounded-full bg-background shadow-lg ring-0 transition-transform",
            "data-checked:translate-x-4 data-unchecked:translate-x-0",
          )}
        />
      </KSwitch.Control>
      {local.children}
    </KSwitch>
  );
}

const SwitchInput = KSwitch.Input;
const SwitchControl = KSwitch.Control;
const SwitchThumb = KSwitch.Thumb;
const SwitchLabel = KSwitch.Label;
const SwitchDescription = KSwitch.Description;
const SwitchErrorMessage = KSwitch.ErrorMessage;

export {
  Switch,
  SwitchInput,
  SwitchControl,
  SwitchThumb,
  SwitchLabel,
  SwitchDescription,
  SwitchErrorMessage,
};
export type { SwitchProps };
