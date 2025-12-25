import { useWTForm } from "@/components/wtform";
import { Save, RotateCcw } from "lucide-solid";
import {
  SpecialCreateFormSchema,
  SpecialUpdateFormSchema,
  type SpecialCreateFormValues,
  type SpecialUpdateFormValues,
} from "@/lib/api";

interface CreateModeProps {
  mode: "create";
  defaultValues: SpecialCreateFormValues;
  onSubmit: (values: SpecialCreateFormValues) => Promise<void>;
  submitText?: string;
}

interface EditModeProps {
  mode: "edit";
  defaultValues: SpecialUpdateFormValues;
  onSubmit: (values: SpecialUpdateFormValues) => Promise<void>;
  submitText?: string;
}

type SpecialFormProps = CreateModeProps | EditModeProps;

export default function SpecialForm(props: SpecialFormProps) {
  const schema =
    props.mode === "create" ? SpecialCreateFormSchema : SpecialUpdateFormSchema;

  const form = useWTForm<SpecialCreateFormValues | SpecialUpdateFormValues>(() => ({
    defaultValues: props.defaultValues,
    validators: {
      onMount: schema,
      onChange: schema,
    },
    onSubmit: async ({ value }) => {
      if (props.mode === "create") {
        await props.onSubmit(value as SpecialCreateFormValues);
      } else {
        await props.onSubmit(value as SpecialUpdateFormValues);
      }
    },
  }));

  return (
    <form.Form class="max-w-2xl mx-auto space-y-6">
      {/* 基本信息卡片 */}
      <div class="bg-card rounded-lg border border-border shadow-sm">
        <div class="p-5">
          <h2 class="text-lg font-semibold mb-4">基本信息</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <form.StringField
              name="name"
              label="名称"
              placeholder="请输入专题名称"
            />
            <form.StringField
              name="slug"
              label="标识"
              placeholder="请输入专题标识（英文、数字、连字符）"
            />
            <form.StringField
              name="title"
              label="标题"
              placeholder="请输入专题标题"
            />
            <form.NumberField
              name="priority"
              label="优先级"
              placeholder="数值越大越靠前"
              min={0}
            />
          </div>
        </div>
      </div>

      {/* 描述信息卡片 */}
      <div class="bg-card rounded-lg border border-border shadow-sm">
        <div class="p-5">
          <h2 class="text-lg font-semibold mb-4">描述信息</h2>
          <form.TextareaField
            name="description"
            label="专题描述"
            placeholder="请输入专题描述..."
            rows={4}
          />
          <div class="mt-4">
            <form.StringField
              name="cover_url"
              label="封面图片"
              placeholder="请输入封面图片URL"
            />
          </div>
        </div>
      </div>


      {/* 状态设置卡片 */}
      <div class="bg-card rounded-lg border border-border shadow-sm">
        <div class="p-5">
          <h2 class="text-lg font-semibold mb-4">状态设置</h2>
          <div class="space-y-4">
            <form.SwitchField
              name="is_active"
              label="上线状态"
              description="关闭后专题将不会在前台显示"
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
