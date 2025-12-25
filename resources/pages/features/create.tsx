import { useNavigate } from "@solidjs/router";

import { feature, type FeatureCreateFormValues } from "@/lib/api";
import { toast } from "@/components/ui/toast";
import FeatureForm from "./components/form";

const defaultValues: FeatureCreateFormValues = {
  name: "",
};

export default function CreateFeature() {
  const navigate = useNavigate();

  const handleSubmit = async (values: FeatureCreateFormValues) => {
    await feature.create(values);
    toast.success("推荐位创建成功");
    navigate("/features");
  };

  return (
    <FeatureForm
      mode="create"
      defaultValues={defaultValues}
      onSubmit={handleSubmit}
      submitText="创建推荐位"
    />
  );
}
