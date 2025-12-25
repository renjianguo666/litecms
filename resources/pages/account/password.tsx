import { Save, KeyRound, Eye, EyeOff } from "lucide-solid";
import { createSignal } from "solid-js";

import { account, PasswordChangeFormSchema } from "@/lib/api";
import { useWTForm } from "@/components/wtform";
import { toast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";

export default function ChangePassword() {
  const [showOldPassword, setShowOldPassword] = createSignal(false);
  const [showNewPassword, setShowNewPassword] = createSignal(false);
  const [showConfirmPassword, setShowConfirmPassword] = createSignal(false);

  const form = useWTForm(() => ({
    defaultValues: {
      old_password: "",
      new_password: "",
      confirm_password: "",
    },
    validators: {
      onMount: PasswordChangeFormSchema,
      onChange: PasswordChangeFormSchema,
    },
    onSubmit: async ({ value }) => {
      await account.changePassword({
        old_password: value.old_password,
        new_password: value.new_password,
      });
      toast.success("密码修改成功");
      form.reset();
    },
  }));

  return (
    <form.Form class="max-w-xl mx-auto space-y-6">
      <div class="bg-card rounded-lg border shadow-sm">
        <div class="p-6">
          <div class="flex items-center gap-3 mb-6">
            <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
              <KeyRound class="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 class="text-lg font-semibold">修改密码</h2>
              <p class="text-sm text-muted-foreground">
                请输入当前密码和新密码
              </p>
            </div>
          </div>

          <div class="space-y-4">
            <div class="relative">
              <form.StringField
                name="old_password"
                label="当前密码"
                type={showOldPassword() ? "text" : "password"}
                placeholder="请输入当前密码"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                class="absolute right-0 top-6 h-10 w-10"
                onClick={() => setShowOldPassword(!showOldPassword())}
              >
                {showOldPassword() ? (
                  <EyeOff class="h-4 w-4" />
                ) : (
                  <Eye class="h-4 w-4" />
                )}
              </Button>
            </div>

            <div class="relative">
              <form.StringField
                name="new_password"
                label="新密码"
                type={showNewPassword() ? "text" : "password"}
                placeholder="请输入新密码 (至少6个字符)"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                class="absolute right-0 top-6 h-10 w-10"
                onClick={() => setShowNewPassword(!showNewPassword())}
              >
                {showNewPassword() ? (
                  <EyeOff class="h-4 w-4" />
                ) : (
                  <Eye class="h-4 w-4" />
                )}
              </Button>
            </div>

            <div class="relative">
              <form.StringField
                name="confirm_password"
                label="确认新密码"
                type={showConfirmPassword() ? "text" : "password"}
                placeholder="请再次输入新密码"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                class="absolute right-0 top-6 h-10 w-10"
                onClick={() => setShowConfirmPassword(!showConfirmPassword())}
              >
                {showConfirmPassword() ? (
                  <EyeOff class="h-4 w-4" />
                ) : (
                  <Eye class="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div class="flex justify-end">
        <form.SubmitButton class="gap-2">
          <Save class="size-4" />
          确认修改
        </form.SubmitButton>
      </div>
    </form.Form>
  );
}
