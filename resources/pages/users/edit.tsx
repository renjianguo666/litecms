import { createResource, Show } from "solid-js";
import { useNavigate, useParams } from "@solidjs/router";
import { Loader } from "lucide-solid";

import { user, type UserUpdateFormValues } from "@/lib/api";
import { toast } from "@/components/ui/toast";
import UserForm from "./components/form";

export default function EditUser() {
  const navigate = useNavigate();

  // 从路由获取参数
  const params = useParams<{ id: string }>();

  // 获取用户详情
  const [userData] = createResource(() => params.id, user.get);

  const handleSubmit = async (values: UserUpdateFormValues) => {
    try {
      await user.update(params.id, values);
      toast.success("用户更新成功");
      navigate("/users");
    } catch (error) {
      toast.error("更新用户失败");
    }
  };

  // 将 API 返回的数据转换为表单需要的格式
  const getDefaultValues = (): UserUpdateFormValues => {
    const data = userData()!;
    return {
      username: data.username,
      email: data.email,
      is_active: data.is_active,
      // roles 需要从对象数组转换为 ID 字符串数组
      roles: data.roles?.map((role) => role.id),
    };
  };

  return (
    <Show
      when={!userData.loading && userData()}
      fallback={
        <div class="flex min-h-[400px] items-center justify-center">
          <Loader class="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      }
    >
      <UserForm
        mode="edit"
        defaultValues={getDefaultValues()}
        onSubmit={handleSubmit}
        submitText="保存修改"
      />
    </Show>
  );
}
