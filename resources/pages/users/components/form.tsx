import { createResource } from "solid-js";
import { useWTForm } from "@/components/wtform";
import { Save, RotateCcw } from "lucide-solid";
import {
  UserCreateFormSchema,
  UserUpdateFormSchema,
  type UserCreateFormValues,
  type UserUpdateFormValues,
  role,
} from "@/lib/api";

interface CreateModeProps {
  mode: "create";
  defaultValues: UserCreateFormValues;
  onSubmit: (values: UserCreateFormValues) => Promise<void>;
  submitText?: string;
}

interface EditModeProps {
  mode: "edit";
  defaultValues: UserUpdateFormValues;
  onSubmit: (values: UserUpdateFormValues) => Promise<void>;
  submitText?: string;
}

type UserFormProps = CreateModeProps | EditModeProps;

export default function UserForm(props: UserFormProps) {
  const [roles] = createResource(async () => {
    const res = await role.list({ page_size: 100 });
    return res.items ?? [];
  });

  const schema =
    props.mode === "create" ? UserCreateFormSchema : UserUpdateFormSchema;

  const form = useWTForm<UserCreateFormValues | UserUpdateFormValues>(() => ({
    defaultValues: props.defaultValues,
    validators: {
      onMount: schema,
      onChange: schema,
    },
    onSubmit: async ({ value }) => {
      if (props.mode === "create") {
        await props.onSubmit(value as UserCreateFormValues);
      } else {
        await props.onSubmit(value as UserUpdateFormValues);
      }
    },
  }));

  const roleOptions = () =>
    (roles() ?? []).map((r) => ({
      label: r.name,
      value: r.id,
    }));

  return (
    <form.Form class="space-y-6">
      <div class="rounded-lg border bg-card p-6">
        <h3 class="mb-4 text-lg font-medium">账户信息</h3>
        <div class="space-y-4">
          <form.StringField
            name="username"
            label="用户名"
            placeholder="请输入用户名"
          />
          <form.StringField
            name="email"
            label="邮箱"
            type="email"
            placeholder="请输入邮箱地址"
          />
          <form.StringField
            name="password"
            label={props.mode === "create" ? "密码" : "新密码"}
            type="password"
            placeholder={
              props.mode === "create" ? "请输入密码" : "留空则不修改"
            }
          />
        </div>
      </div>

      <div class="rounded-lg border bg-card p-6">
        <h3 class="mb-4 text-lg font-medium">权限设置</h3>
        <div class="space-y-4">
          {props.mode === "create" ? (
            <form.CheckboxField
              name="is_superuser"
              label="超级管理员"
              description="拥有系统所有权限"
            />
          ) : (
            <form.SwitchField
              name="is_active"
              label="启用账户"
              description="关闭后用户将无法登录"
            />
          )}
          <form.ComboboxField
            name="roles"
            label="分配角色"
            options={roleOptions()}
            placeholder="选择角色..."
            searchPlaceholder="搜索角色..."
          />
        </div>
      </div>

      <div class="flex justify-end gap-3">
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
