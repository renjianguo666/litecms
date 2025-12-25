import { Button } from "@/components/ui";
import { useFormContext } from "../context";
import type { ResetButtonProps } from "../types";

export function ResetButton(props: ResetButtonProps) {
  const form = useFormContext();

  return (
    <Button
      type="button"
      variant={props.variant ?? "outline"}
      class={props.class}
      onClick={() => form.reset()}
    >
      {props.children ?? "重置"}
    </Button>
  );
}
