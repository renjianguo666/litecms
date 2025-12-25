import { Show } from "solid-js";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
  Label,
} from "@/components/ui";
import { useFieldContext } from "../context";
import type { SelectFieldProps, SelectOption } from "../types";

export function SelectField(props: SelectFieldProps) {
  const field = useFieldContext<string | null>();

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

  // 将字符串值转换为选项对象
  const selectedOption = () =>
    props.options.find((opt) => opt.value === field().state.value);

  return (
    <div class="flex flex-col gap-1.5 w-full">
      <Show when={props.label}>
        <Label for={field().name}>{props.label}</Label>
      </Show>

      <Select<SelectOption>
        value={selectedOption()}
        options={props.options}
        optionValue="value"
        optionTextValue="label"
        onChange={(option) => {
          const value = option?.value ?? "";
          field().handleChange(props.nullable && value === "" ? null : value);
        }}
        disabled={props.disabled}
        placeholder={props.placeholder ?? "请选择..."}
        itemComponent={(itemProps) => (
          <SelectItem item={itemProps.item}>
            {itemProps.item.rawValue.label}
          </SelectItem>
        )}
      >
        <SelectTrigger
          id={field().name}
          onBlur={() => field().handleBlur()}
          aria-invalid={hasError()}
          class="w-full"
        >
          <SelectValue<SelectOption>>
            {(state) => state.selectedOption()?.label}
          </SelectValue>
        </SelectTrigger>

        <SelectContent />
      </Select>

      <Show when={props.description && !hasError()}>
        <p class="text-xs text-muted-foreground">{props.description}</p>
      </Show>

      <Show when={hasError()}>
        <p class="text-xs text-destructive">{errorMessages()}</p>
      </Show>
    </div>
  );
}
