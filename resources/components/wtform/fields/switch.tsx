import { Show } from "solid-js";
import { Switch, SwitchLabel } from "@/components/ui";
import { useFieldContext } from "../context";
import type { SwitchFieldProps } from "../types";

export function SwitchField(props: SwitchFieldProps) {
  const field = useFieldContext<boolean>();

  const hasError = () => {
    const f = field();
    return f.state.meta.isTouched && f.state.meta.errors.length > 0;
  };

  const errorMessages = () => {
    const f = field();
    return f.state.meta.errors
      .map((e: any) => (typeof e === "string" ? e : (e?.message ?? "")))
      .join(", ");
  };

  return (
    <div class="flex flex-col gap-2">
      <div class="flex items-center justify-between gap-4">
        <div class="grid gap-1.5 leading-none">
          <Show when={props.description}>
            <p class="text-sm text-muted-foreground">{props.description}</p>
          </Show>
        </div>

        <Switch
          checked={field().state.value ?? false}
          onChange={(checked: boolean) => field().handleChange(checked)}
          disabled={props.disabled}
          aria-invalid={hasError()}
        >
          <SwitchLabel>{props.label}</SwitchLabel>
        </Switch>
      </div>

      <Show when={hasError()}>
        <p class="text-sm text-destructive">{errorMessages()}</p>
      </Show>
    </div>
  );
}
