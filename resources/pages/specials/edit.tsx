import { createResource, Show } from "solid-js";
import { useNavigate, useParams } from "@solidjs/router";
import { Loader } from "lucide-solid";

import { special, type SpecialUpdateFormValues } from "@/lib/api";
import { toast } from "@/components/ui/toast";
import SpecialForm from "./components/form";

export default function EditSpecial() {
  const navigate = useNavigate();

  // 从路由获取参数
  const params = useParams<{ id: string }>();

  // 获取专题详情
  const [specialData] = createResource(() => params.id, special.get);

  const handleSubmit = async (values: SpecialUpdateFormValues) => {
    await special.update(params.id, values);
    toast.success("专题更新成功");
    navigate("/specials");
  };

  return (
    <Show
      when={!specialData.loading && specialData()}
      fallback={
        <div class="flex min-h-[400px] items-center justify-center">
          <Loader class="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      }
    >
      <SpecialForm
        mode="edit"
        defaultValues={specialData()!}
        onSubmit={handleSubmit}
        submitText="保存修改"
      />
    </Show>
  );
}
