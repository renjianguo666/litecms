import { Show } from "solid-js";
import { Loader2 } from "lucide-solid";
import { Button } from "@/components/ui";
import { useFormContext } from "../context";
import type { SubmitButtonProps } from "../types";

export function SubmitButton(props: SubmitButtonProps) {
  const form = useFormContext();

  const canSubmit = form.useStore((state) => state.canSubmit);
  const isSubmitting = form.useStore((state) => state.isSubmitting);

  return (
    <Button
      type="submit"
      disabled={!canSubmit() || isSubmitting()}
      class={props.class}
    >
      <Show when={isSubmitting()} fallback={props.children ?? "提交"}>
        <Loader2 class="size-4 animate-spin" />
        提交中...
      </Show>
    </Button>
  );
}
