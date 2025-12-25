import { useSearchParams, useNavigate } from "@solidjs/router";
import { Plus } from "lucide-solid";

import DataTable, { type TableQueryParams } from "@/components/datatable";
import { Button } from "@/components/ui/button";
import { article } from "@/lib/api";
import { columns } from "./components/table-columns";
import { RequirePermission } from "@/components/require-permission";

export default function Articles() {
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
        fetcher={article.list}
        queryParams={getQueryParams()}
        onChange={handleChange}
        searchPlaceholder="搜索文章标题..."
        toolbarActions={
          <RequirePermission permission="articles:create_article">
            <Button size="sm" onClick={() => navigate("/articles/create")}>
              <Plus class="size-4" />
              新建文章
            </Button>
          </RequirePermission>
        }
      />
    </div>
  );
}

