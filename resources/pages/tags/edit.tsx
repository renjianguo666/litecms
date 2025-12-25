import { createResource, Show } from "solid-js";
import { useNavigate, useParams } from "@solidjs/router";
import { Loader } from "lucide-solid";

import { tag, type TagUpdateFormValues } from "@/lib/api";
import { toast } from "@/components/ui/toast";
import TagForm from "./components/form";

export default function EditTag() {
  const navigate = useNavigate();

  // 从路由获取参数
  const params = useParams<{ id: string }>();

  // 获取标签详情
  const [tagData] = createResource(() => params.id, tag.get);

  const handleSubmit = async (values: TagUpdateFormValues) => {
    await tag.update(params.id, values);
    toast.success("标签更新成功");
    navigate("/tags");
  };

  return (
    <Show
      when={!tagData.loading && tagData()}
      fallback={
        <div class="flex min-h-[400px] items-center justify-center">
          <Loader class="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      }
    >
      <TagForm
        mode="edit"
        defaultValues={tagData()!}
        onSubmit={handleSubmit}
        submitText="保存修改"
      />
    </Show>
  );
}
