import { useNavigate } from "@solidjs/router";

import { role, type RoleCreateFormValues } from "@/lib/api";
import { toast } from "@/components/ui/toast";
import RoleForm from "./components/form";

const defaultValues: RoleCreateFormValues = {
  name: "",
  description: "",
  permissions: [],
};

export default function CreateRole() {
  const navigate = useNavigate();


  const handleSubmit = async (values: RoleCreateFormValues) => {
    await role.create(values);
    toast.success("角色创建成功");
    navigate("/roles");
  };

  return (
    <RoleForm
      mode="create"
      defaultValues={defaultValues}
      onSubmit={handleSubmit}
      submitText="创建角色"
    />
  );
}
