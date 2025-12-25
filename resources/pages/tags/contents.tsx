import { createResource, Show } from "solid-js";
import { A, useParams } from "@solidjs/router";
import { ArrowLeft, Loader } from "lucide-solid";

import { tag } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import TagContents from "./components/contents";

export default function TagContentsPage() {
  const params = useParams<{ id: string }>();

  // 获取标签信息
  const [tagData] = createResource(() => params.id, tag.get);

  return (
    <div class="mx-auto max-w-4xl space-y-6">
      {/* 返回链接 */}
      <div>
        <Button as={A} href="/tags" variant="ghost" size="sm">
          <ArrowLeft class="mr-2 h-4 w-4" />
          返回标签列表
        </Button>
      </div>

      <Show
        when={!tagData.loading && tagData()}
        fallback={
          <div class="flex min-h-[400px] items-center justify-center">
            <Loader class="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        }
      >
        {/* 标签信息头部 */}
        <Card>
          <CardHeader>
            <div class="flex items-start justify-between">
              <div class="space-y-1">
                <CardTitle>{tagData()!.name}</CardTitle>
                <CardDescription>
                  <Badge variant="secondary" class="font-mono text-xs">
                    {tagData()!.slug}
                  </Badge>
                </CardDescription>
              </div>
              <Button
                as={A}
                href={`/tags/${params.id}`}
                variant="outline"
                size="sm"
              >
                编辑标签
              </Button>
            </div>
          </CardHeader>
        </Card>

        {/* 内容管理组件 */}
        <Card>
          <CardHeader>
            <CardTitle>内容管理</CardTitle>
            <CardDescription>管理与此标签关联的内容</CardDescription>
          </CardHeader>
          <CardContent>
            <TagContents tagId={params.id} />
          </CardContent>
        </Card>
      </Show>
    </div>
  );
}
