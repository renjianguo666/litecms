import { useNavigate } from "@solidjs/router";

import { user, type UserCreateFormValues } from "@/lib/api";
import { toast } from "@/components/ui/toast";
import UserForm from "./components/form";

const defaultValues: UserCreateFormValues = {
  username: "",
  email: "",
  password: "",
  is_superuser: false,
  roles: [],
};

export default function CreateUser() {
  const navigate = useNavigate();
  

  const handleSubmit = async (values: UserCreateFormValues) => {
    try {
      await user.create(values);
      toast.success("用户创建成功");
      navigate("/users");
    } catch (error) {
      toast.error("创建用户失败");
    }
  };

  return (
    <UserForm
      mode="create"
      defaultValues={defaultValues}
      onSubmit={handleSubmit}
      submitText="创建用户"
    />
  );
}
