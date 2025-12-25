import { Show } from "solid-js";
import { Textarea, Label } from "@/components/ui";
import { useFieldContext } from "../context";
import type { TextareaFieldProps } from "../types";

export function TextareaField(props: TextareaFieldProps) {
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
    <div class="flex flex-col gap-1.5 w-full">
      <Show when={props.label}>
        <Label for={field().name}>{props.label}</Label>
      </Show>

      <Textarea
        id={field().name}
        value={field().state.value ?? ""}
        onInput={(e) => field().handleChange(e.currentTarget.value)}
        onBlur={() => field().handleBlur()}
        placeholder={props.placeholder}
        rows={props.rows ?? 3}
        disabled={props.disabled}
        aria-invalid={hasError()}
      />

      <Show when={props.description && !hasError()}>
        <p class="text-xs text-muted-foreground">{props.description}</p>
      </Show>

      <Show when={hasError()}>
        <p class="text-xs text-destructive">{errorMessages()}</p>
      </Show>
    </div>
  );
}
