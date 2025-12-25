import { Show } from "solid-js";
import { Input, Label } from "@/components/ui";
import { useFieldContext } from "../context";
import type { StringFieldProps } from "../types";

export function StringField(props: StringFieldProps) {
  const field = useFieldContext<string>();

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
    <div class="flex flex-col gap-2 w-full">
      <Show when={props.label}>
        <Label for={field().name}>{props.label}</Label>
      </Show>

      <Input
        id={field().name}
        type={props.type ?? "text"}
        value={field().state.value ?? ""}
        onInput={(e) => field().handleChange(e.currentTarget.value)}
        onBlur={() => field().handleBlur()}
        placeholder={props.placeholder}
        disabled={props.disabled}
        autocomplete="off"
        aria-invalid={hasError()}
      />

      <Show when={props.description && !hasError()}>
        <p class="text-sm text-muted-foreground">{props.description}</p>
      </Show>

      <Show when={hasError()}>
        <p class="text-sm text-destructive">{errorMessages()}</p>
      </Show>
    </div>
  );
}
