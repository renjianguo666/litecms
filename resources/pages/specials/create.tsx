import { useNavigate } from "@solidjs/router";

import { special, type SpecialCreateFormValues } from "@/lib/api";
import { toast } from "@/components/ui/toast";
import SpecialForm from "./components/form";

const defaultValues: SpecialCreateFormValues = {
  name: "",
  slug: "",
  title: "",
  description: undefined,
  cover_url: undefined,
  is_active: true,
  priority: 0,
};

export default function CreateSpecial() {
  const navigate = useNavigate();

  const handleSubmit = async (values: SpecialCreateFormValues) => {
    await special.create(values);
    toast.success("专题创建成功");
    navigate("/specials");
  };

  return (
    <SpecialForm
      mode="create"
      defaultValues={defaultValues}
      onSubmit={handleSubmit}
      submitText="创建专题"
    />
  );
}
