import { Show } from "solid-js";
import { Checkbox, CheckboxLabel } from "@/components/ui";
import { useFieldContext } from "../context";
import type { CheckboxFieldProps } from "../types";

export function CheckboxField(props: CheckboxFieldProps) {
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
      <Checkbox
        id={field().name}
        checked={field().state.value ?? false}
        onChange={(checked: boolean) => field().handleChange(checked)}
        disabled={props.disabled}
        aria-invalid={hasError()}
      >
        <CheckboxLabel class="flex flex-col gap-1">
          <span>{props.label}</span>
          <Show when={props.description}>
            <span class="text-sm text-muted-foreground font-normal">
              {props.description}
            </span>
          </Show>
        </CheckboxLabel>
      </Checkbox>

      <Show when={hasError()}>
        <p class="text-sm text-destructive">{errorMessages()}</p>
      </Show>
    </div>
  );
}
