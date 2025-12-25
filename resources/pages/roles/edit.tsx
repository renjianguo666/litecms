import { createResource, Show } from "solid-js";
import { useNavigate, useParams } from "@solidjs/router";
import { Loader } from "lucide-solid";

import { role, type RoleUpdateFormValues } from "@/lib/api";
import { toast } from "@/components/ui/toast";
import RoleForm from "./components/form";

export default function EditRole() {
  const navigate = useNavigate();

  // 从路由获取参数
  const params = useParams<{ id: string }>();

  // 获取角色详情
  const [roleData] = createResource(() => params.id, role.get);

  const handleSubmit = async (values: RoleUpdateFormValues) => {
    await role.update(params.id, values);
    toast.success("角色更新成功");
    navigate("/roles");
  };

  // 将 API 返回的数据转换为表单需要的格式
  const getDefaultValues = (): RoleUpdateFormValues => {
    const data = roleData()!;
    return {
      name: data.name,
      description: data.description ?? "",
      // permissions 需要从对象数组转换为 ID 字符串数组
      permissions: data.permissions?.map((p) => p.id),
    };
  };

  return (
    <Show
      when={!roleData.loading && roleData()}
      fallback={
        <div class="flex min-h-[400px] items-center justify-center">
          <Loader class="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      }
    >
      <RoleForm
        mode="edit"
        defaultValues={getDefaultValues()}
        onSubmit={handleSubmit}
        submitText="保存修改"
      />
    </Show>
  );
}
