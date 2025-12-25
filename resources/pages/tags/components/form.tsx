import { useWTForm } from "@/components/wtform";
import { Save, RotateCcw } from "lucide-solid";
import {
  TagCreateFormSchema,
  TagUpdateFormSchema,
  type TagCreateFormValues,
  type TagUpdateFormValues,
} from "@/lib/api";

interface CreateModeProps {
  mode: "create";
  defaultValues: TagCreateFormValues;
  onSubmit: (values: TagCreateFormValues) => Promise<void>;
  submitText?: string;
}

interface EditModeProps {
  mode: "edit";
  defaultValues: TagUpdateFormValues;
  onSubmit: (values: TagUpdateFormValues) => Promise<void>;
  submitText?: string;
}

type TagFormProps = CreateModeProps | EditModeProps;

export default function TagForm(props: TagFormProps) {
  const schema =
    props.mode === "create" ? TagCreateFormSchema : TagUpdateFormSchema;

  const form = useWTForm<TagCreateFormValues | TagUpdateFormValues>(() => ({
    defaultValues: props.defaultValues,
    validators: {
      onMount: schema,
      onChange: schema,
    },
    onSubmit: async ({ value }) => {
      if (props.mode === "create") {
        await props.onSubmit(value as TagCreateFormValues);
      } else {
        await props.onSubmit(value as TagUpdateFormValues);
      }
    },
  }));

  return (
    <form.Form class="max-w-2xl mx-auto space-y-6">
      {/* 基本信息卡片 */}
      <div class="bg-card rounded-lg border border-border shadow-sm">
        <div class="p-5">
          <h2 class="text-lg font-semibold mb-4">标签信息</h2>
          <div class="grid grid-cols-1 gap-4">
            <form.StringField
              name="name"
              label="名称"
              placeholder="请输入标签名称"
            />
            <form.StringField
              name="slug"
              label="标识"
              placeholder="请输入标签标识（英文、数字、连字符）"
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
