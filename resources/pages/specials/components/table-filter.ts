import type { FilterConfig } from "@/components/datatable";

export const filterConfig: FilterConfig[] = [
  {
    name: "is_active",
    variant: "boolean",
    label: "状态",
    trueText: "上线",
    falseText: "下线",
  },
];
