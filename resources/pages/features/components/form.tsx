import { useWTForm } from "@/components/wtform";
import { Save, RotateCcw } from "lucide-solid";
import {
  FeatureCreateFormSchema,
  FeatureUpdateFormSchema,
  type FeatureCreateFormValues,
  type FeatureUpdateFormValues,
} from "@/lib/api";

interface CreateModeProps {
  mode: "create";
  defaultValues: FeatureCreateFormValues;
  onSubmit: (values: FeatureCreateFormValues) => Promise<void>;
  submitText?: string;
}

interface EditModeProps {
  mode: "edit";
  defaultValues: FeatureUpdateFormValues;
  onSubmit: (values: FeatureUpdateFormValues) => Promise<void>;
  submitText?: string;
}

type FeatureFormProps = CreateModeProps | EditModeProps;

export default function FeatureForm(props: FeatureFormProps) {
  const schema =
    props.mode === "create" ? FeatureCreateFormSchema : FeatureUpdateFormSchema;

  const form = useWTForm<FeatureCreateFormValues | FeatureUpdateFormValues>(
    () => ({
      defaultValues: props.defaultValues,
      validators: {
        onMount: schema,
        onChange: schema,
      },
      onSubmit: async ({ value }) => {
        if (props.mode === "create") {
          await props.onSubmit(value as FeatureCreateFormValues);
        } else {
          await props.onSubmit(value as FeatureUpdateFormValues);
        }
      },
    }),
  );

  return (
    <form.Form class="max-w-2xl mx-auto space-y-6">
      {/* 基本信息卡片 */}
      <div class="bg-card rounded-lg border border-border shadow-sm">
        <div class="p-5">
          <h2 class="text-lg font-semibold mb-4">推荐位信息</h2>
          <div class="grid grid-cols-1 gap-4">
            <form.StringField
              name="name"
              label="名称"
              placeholder="请输入推荐位名称"
            />
          </div>
        </div>
      </div>

      {/* 操作按钮 */}
      <div class="flex justify-end gap-3 pt-4">
        <form.ResetButton class="gap-2">
          <RotateCcw class="size-4" />
          重置
        </form.ResetButton>
        <form.SubmitButton class="gap-2">
          <Save class="size-4" />
          {props.submitText ?? "保存"}
        </form.SubmitButton>
      </div>
    </form.Form>
  );
}
