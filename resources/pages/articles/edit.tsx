import { createResource, Show } from "solid-js";
import { useNavigate, useParams } from "@solidjs/router";
import { Loader } from "lucide-solid";

import { article, type ArticleUpdateFormValues } from "@/lib/api";
import { toast } from "@/components/ui/toast";
import ArticleForm from "./components/form";

export default function EditArticle() {
  const navigate = useNavigate();

  // 从路由获取参数
  const params = useParams<{ id: string }>();

  // 获取文章详情
  const [articleData] = createResource(() => params.id, article.get);

  const handleSubmit = async (values: ArticleUpdateFormValues) => {
    await article.update(params.id, values);
    toast.success("文章更新成功");
    navigate("/articles");
  };

  return (
    <Show
      when={!articleData.loading && articleData()}
      fallback={
        <div class="flex min-h-[400px] items-center justify-center">
          <Loader class="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      }
    >
      <ArticleForm
        mode="edit"
        defaultValues={{
          title: articleData()!.title,
          category_id: articleData()!.category_id,
          content: articleData()!.content,
          description: articleData()!.description ?? "",
          cover_url: articleData()!.cover_url ?? "",
          status: articleData()!.status,
          published_at: articleData()!.published_at,
          tag_ids: articleData()!.tags?.map((t) => t.id) ?? [],
          special_ids: articleData()!.specials?.map((t) => t.id) ?? [],
          feature_ids: articleData()!.features?.map((f) => f.id) ?? [],
        }}
        onSubmit={handleSubmit}
        submitText="保存修改"
      />
    </Show>
  );
}
