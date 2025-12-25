import { useNavigate } from "@solidjs/router";

import { article, type ArticleCreateFormValues } from "@/lib/api";
import { toast } from "@/components/ui/toast";
import ArticleForm from "./components/form";

const defaultValues: ArticleCreateFormValues = {
  title: "",
  category_ids: [],
  text: "",
  description: "",
  cover_url: "",
  source: "",
  author: "",
  tag_ids: [],
  special_ids: [],
  feature_ids: [],
  published_at: new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString(),
};

export default function CreateArticle() {
  const navigate = useNavigate();

  const handleSubmit = async (values: ArticleCreateFormValues) => {
    await article.create(values);
    toast.success("文章创建成功");
    navigate("/articles");
  };

  return (
    <ArticleForm
      mode="create"
      defaultValues={defaultValues}
      onSubmit={handleSubmit}
      submitText="发布文章"
    />
  );
}
