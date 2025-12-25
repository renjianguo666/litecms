import { useNavigate } from "@solidjs/router";

import { tag, type TagCreateFormValues } from "@/lib/api";
import { toast } from "@/components/ui/toast";
import TagForm from "./components/form";

const defaultValues: TagCreateFormValues = {
  name: "",
  slug: "",
};

export default function CreateTag() {
  const navigate = useNavigate();


  const handleSubmit = async (values: TagCreateFormValues) => {
    await tag.create(values);
    toast.success("标签创建成功");
    navigate("/tags");
  };

  return (
    <TagForm
      mode="create"
      defaultValues={defaultValues}
      onSubmit={handleSubmit}
      submitText="创建标签"
    />
  );
}
