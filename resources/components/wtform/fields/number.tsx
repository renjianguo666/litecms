import { Show } from "solid-js";
import { Input, Label } from "@/components/ui";
import { useFieldContext } from "../context";
import type { NumberFieldProps } from "../types";

export function NumberField(props: NumberFieldProps) {
  const field = useFieldContext<number | undefined>();

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

  // 将数值转为字符串显示
  const stringValue = () => {
    const val = field().state.value;
    return val === undefined || val === null ? "" : String(val);
  };

  const handleInput = (e: InputEvent & { currentTarget: HTMLInputElement }) => {
    const value = e.currentTarget.value;
    field().handleChange(value === "" ? undefined : Number(value));
  };

  return (
    <div class="flex flex-col gap-1.5 w-full">
      <Show when={props.label}>
        <Label for={field().name}>{props.label}</Label>
      </Show>

      <Input
        id={field().name}
        type="number"
        value={stringValue()}
        onInput={handleInput}
        onBlur={() => field().handleBlur()}
        placeholder={props.placeholder}
        min={props.min}
        max={props.max}
        step={props.step}
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
