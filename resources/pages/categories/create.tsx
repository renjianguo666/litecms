import { useNavigate } from "@solidjs/router";

import { category, type CategoryCreateFormValues } from "@/lib/api";
import { toast } from "@/components/ui/toast";
import CategoryForm from "./components/form";

const defaultValues: CategoryCreateFormValues = {
  name: "",
  path: "",
  content_path: "/p/{key:12}.html",
  title: undefined,
  description: undefined,
  cover_url: undefined,
  page_size: 10,
  priority: 0,
  template: "default",
  parent_id: null,
  domain: "",
};

export default function CreateCategory() {
  const navigate = useNavigate();

  const handleSubmit = async (values: CategoryCreateFormValues) => {
    await category.create(values);
    toast.success("分类创建成功");
    navigate("/categories");
  };

  return (
    <CategoryForm
      mode="create"
      defaultValues={defaultValues}
      onSubmit={handleSubmit}
      submitText="创建分类"
    />
  );
}
