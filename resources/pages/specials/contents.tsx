import { createResource, Show } from "solid-js";
import { A, useParams } from "@solidjs/router";
import { ArrowLeft, Loader } from "lucide-solid";

import { special } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import SpecialContents from "./components/contents";

export default function SpecialContentsPage() {
  const params = useParams<{ id: string }>();

  // 获取专题信息
  const [specialData] = createResource(() => params.id, special.get);

  return (
    <div class="mx-auto max-w-4xl space-y-6">
      {/* 返回链接 */}
      <div>
        <Button as={A} href="/specials" variant="ghost" size="sm">
          <ArrowLeft class="mr-2 h-4 w-4" />
          返回专题列表
        </Button>
      </div>

      <Show
        when={!specialData.loading && specialData()}
        fallback={
          <div class="flex min-h-[400px] items-center justify-center">
            <Loader class="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        }
      >
        {/* 专题信息头部 */}
        <Card>
          <CardHeader>
            <div class="flex items-start justify-between">
              <div class="space-y-1">
                <CardTitle>{specialData()!.name}</CardTitle>
                <CardDescription>
                  {specialData()!.title || specialData()!.slug}
                </CardDescription>
              </div>
              <Button
                as={A}
                href={`/specials/${params.id}`}
                variant="outline"
                size="sm"
              >
                编辑专题
              </Button>
            </div>
          </CardHeader>
        </Card>

        {/* 内容管理组件 */}
        <Card>
          <CardHeader>
            <CardTitle>内容管理</CardTitle>
            <CardDescription>管理与此专题关联的内容</CardDescription>
          </CardHeader>
          <CardContent>
            <SpecialContents specialId={params.id} />
          </CardContent>
        </Card>
      </Show>
    </div>
  );
}
