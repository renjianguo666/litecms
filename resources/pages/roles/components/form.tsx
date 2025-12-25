import { createResource, Show } from "solid-js";
import { useWTForm } from "@/components/wtform";
import { Save, RotateCcw, Loader } from "lucide-solid";
import {
  RoleCreateFormSchema,
  RoleUpdateFormSchema,
  type RoleCreateFormValues,
  type RoleUpdateFormValues,
  permission,
} from "@/lib/api";
import PermissionCheckboxGrid from "./permission-grid";

interface CreateModeProps {
  mode: "create";
  defaultValues: RoleCreateFormValues;
  onSubmit: (values: RoleCreateFormValues) => Promise<void>;
  submitText?: string;
}

interface EditModeProps {
  mode: "edit";
  defaultValues: RoleUpdateFormValues;
  onSubmit: (values: RoleUpdateFormValues) => Promise<void>;
  submitText?: string;
}

type RoleFormProps = CreateModeProps | EditModeProps;

export default function RoleForm(props: RoleFormProps) {
  // 获取权限列表
  const [permissions] = createResource(async () => {
    const res = await permission.list({ page_size: 100 });
    return res.items ?? [];
  });

  const schema =
    props.mode === "create" ? RoleCreateFormSchema : RoleUpdateFormSchema;

  const form = useWTForm<RoleCreateFormValues | RoleUpdateFormValues>(() => ({
    defaultValues: props.defaultValues,
    validators: {
      onMount: schema,
      onChange: schema,
    },
    onSubmit: async ({ value }) => {
      if (props.mode === "create") {
        await props.onSubmit(value as RoleCreateFormValues);
      } else {
        await props.onSubmit(value as RoleUpdateFormValues);
      }
    },
  }));

  return (
    <form.Form class="max-w-4xl mx-auto space-y-6">
      {/* 基本信息卡片 */}
      <div class="bg-card rounded-lg border border-border shadow-sm">
        <div class="p-5">
          <h2 class="text-lg font-semibold mb-4">角色信息</h2>
          <div class="grid grid-cols-1 gap-4">
            <form.StringField
              name="name"
              label="角色名称"
              placeholder="请输入角色名称"
            />
            <form.TextareaField
              name="description"
              label="角色描述"
              placeholder="请输入角色描述"
              rows={3}
            />
          </div>
        </div>
      </div>

      {/* 权限设置卡片 */}
      <div class="bg-card rounded-lg border border-border shadow-sm">
        <div class="p-5">
          <h2 class="text-lg font-semibold mb-4">权限设置</h2>
          <Show
            when={!permissions.loading}
            fallback={
              <div class="flex items-center justify-center py-8 text-muted-foreground">
                <Loader class="size-5 animate-spin mr-2" />
                加载权限列表...
              </div>
            }
          >
            <form.Field name="permissions">
              {(field) => (
                <PermissionCheckboxGrid
                  permissions={permissions() ?? []}
                  value={(field().state.value as string[]) ?? []}
                  onChange={(value) => field().handleChange(value)}
                />
              )}
            </form.Field>
          </Show>
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

