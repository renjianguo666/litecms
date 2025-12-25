import { createResource, Show } from "solid-js";
import { useNavigate, useParams } from "@solidjs/router";
import { Loader } from "lucide-solid";

import { category, type CategoryUpdateFormValues } from "@/lib/api";
import { toast } from "@/components/ui/toast";
import CategoryForm from "./components/form";

export default function EditCategory() {
  const navigate = useNavigate();

  // 从路由获取参数
  const params = useParams<{ id: string }>();

  // 获取分类详情
  const [categoryData] = createResource(() => params.id, category.get);

  const handleSubmit = async (values: CategoryUpdateFormValues) => {
    await category.update(params.id, values);
    toast.success("分类更新成功");
    navigate("/categories");
  };

  // 将 API 返回的数据转换为表单所需的格式
  const getDefaultValues = (): CategoryUpdateFormValues => {
    const data = categoryData()!;
    return {
      name: data.name,
      path: data.path,
      content_path: data.content_path,
      title: data.title ?? undefined,
      description: data.description ?? undefined,
      cover_url: data.cover_url ?? undefined,
      page_size: data.page_size,
      priority: data.priority,
      template: data.template,
      parent_id: data.parent_id ?? undefined,
      domain: data.domain ?? "",
    };
  };

  return (
    <Show
      when={!categoryData.loading && categoryData()}
      fallback={
        <div class="flex min-h-[400px] items-center justify-center">
          <Loader class="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      }
    >
      <CategoryForm
        mode="edit"
        defaultValues={getDefaultValues()}
        onSubmit={handleSubmit}
        submitText="保存修改"
        disabledId={params.id}
      />
    </Show>
  );
}
