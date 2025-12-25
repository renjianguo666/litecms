import { useNavigate } from "@solidjs/router";
import { useWTForm } from "@/components/wtform";
import { auth } from "@/lib/api";
import { setCurrentUser } from "@/lib/auth";
import { toast } from "@/components/ui/toast";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface LoginFormData {
  username: string;
  password: string;
}

export default function LoginPage() {
  const navigate = useNavigate();

  const form = useWTForm<LoginFormData>(() => ({
    defaultValues: { username: "", password: "" },
    onSubmit: async ({ value }) => {
      const data = await auth.login(value);
      setCurrentUser(data);
      toast.success("验证通过，正在进入系统...");
      setTimeout(() => navigate("/"), 800);
    },
  }));

  return (
    <div class="relative flex min-h-screen items-center justify-center bg-muted/40 px-4">
      {/* 方格背景 */}
      <div class="absolute inset-0 opacity-[0.03] pointer-events-none bg-size-[30px_30px] bg-[linear-gradient(to_right,currentColor_1px,transparent_1px),linear-gradient(to_bottom,currentColor_1px,transparent_1px)] text-foreground" />

      <div class="relative z-10 w-full max-w-md space-y-8">
        {/* Header */}

        {/* Login Card */}
        <Card>
          <CardHeader>
            <div class="flex flex-col space-y-2 text-center mb-5">
              <h1 class="text-3xl font-bold tracking-tight">LiteCMS</h1>
            </div>
            <CardTitle>欢迎回来</CardTitle>
            <CardDescription>请输入您的账号和密码以继续</CardDescription>
          </CardHeader>
          <CardContent>
            <form.Form class="space-y-4">
              <form.StringField
                name="username"
                label="账号"
                placeholder="请输入账号"
              />

              <form.StringField
                name="password"
                label="密码"
                type="password"
                placeholder="请输入密码"
              />

              <form.SubmitButton class="w-full" />
            </form.Form>
          </CardContent>
          <CardFooter class="flex flex-col">
            <p class="text-center text-xs text-muted-foreground">
              技术支持：鼎道网络 · v1.0.0
            </p>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
