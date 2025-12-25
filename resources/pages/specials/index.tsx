import { useSearchParams, useNavigate } from "@solidjs/router";
import { Plus } from "lucide-solid";

import DataTable, { type TableQueryParams } from "@/components/datatable";
import { Button } from "@/components/ui/button";
import { special } from "@/lib/api";
import { RequirePermission } from "@/components/require-permission";

import { columns } from "./components/table-columns";

export default function Specials() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  // 从 URL 读取 search params
  const getQueryParams = (): TableQueryParams => ({
    search:
      typeof searchParams.search === "string" ? searchParams.search : undefined,
    page: Number(searchParams.page) || 1,
    page_size: Number(searchParams.page_size) || 10,
  });

  // 处理参数变化 - 修改 URL search params
  const handleChange = (params: TableQueryParams) => {
    setSearchParams({
      search: params.search || "",
      page: String(params.page ?? 1),
      page_size: String(params.page_size ?? 10),
    });
  };

  return (
    <div class="rounded-lg border bg-card p-3.5 pb-2">
      <DataTable
        columns={columns}
        fetcher={special.list}
        queryParams={getQueryParams()}
        onChange={handleChange}
        searchPlaceholder="搜索专题..."
        toolbarActions={
          <RequirePermission permission="taxonomies:create_special">
            <Button size="sm" onClick={() => navigate("/specials/create")}>
              <Plus class="size-4" />
              添加专题
            </Button>
          </RequirePermission>
        }
      />
    </div>
  );
}
