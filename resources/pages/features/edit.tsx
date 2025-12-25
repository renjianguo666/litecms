import { createResource, Show } from "solid-js";
import { useNavigate, useParams } from "@solidjs/router";
import { Loader } from "lucide-solid";

import { feature, type FeatureUpdateFormValues } from "@/lib/api";
import { toast } from "@/components/ui/toast";
import FeatureForm from "./components/form";

export default function EditFeature() {
  const navigate = useNavigate();

  // 从路由获取参数
  const params = useParams<{ id: string }>();

  // 获取推荐位详情
  const [featureData] = createResource(() => params.id, feature.get);

  const handleSubmit = async (values: FeatureUpdateFormValues) => {
    await feature.update(params.id, values);
    toast.success("推荐位更新成功");
    navigate("/features");
  };

  return (
    <Show
      when={!featureData.loading && featureData()}
      fallback={
        <div class="flex min-h-[400px] items-center justify-center">
          <Loader class="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      }
    >
      <FeatureForm
        mode="edit"
        defaultValues={featureData()!}
        onSubmit={handleSubmit}
        submitText="保存修改"
      />
    </Show>
  );
}
