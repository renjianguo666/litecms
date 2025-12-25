import { createResource, Show } from "solid-js";
import { A, useParams } from "@solidjs/router";
import { ArrowLeft, Loader } from "lucide-solid";

import { feature } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import FeatureContents from "./components/contents";

export default function FeatureContentsPage() {
  const params = useParams<{ id: string }>();

  // 获取推荐位信息
  const [featureData] = createResource(() => params.id, feature.get);

  return (
    <div class="mx-auto max-w-4xl space-y-6">
      {/* 返回链接 */}
      <div>
        <Button as={A} href="/features" variant="ghost" size="sm">
          <ArrowLeft class="mr-2 h-4 w-4" />
          返回推荐位列表
        </Button>
      </div>

      <Show
        when={!featureData.loading && featureData()}
        fallback={
          <div class="flex min-h-[400px] items-center justify-center">
            <Loader class="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        }
      >
        {/* 推荐位信息头部 */}
        <Card>
          <CardHeader>
            <div class="flex items-start justify-between">
              <div class="space-y-1">
                <CardTitle>{featureData()!.name}</CardTitle>
                <CardDescription>
                  <Badge variant="secondary" class="font-mono text-xs">
                    {featureData()!.id}
                  </Badge>
                </CardDescription>
              </div>
              <Button
                as={A}
                href={`/features/${params.id}`}
                variant="outline"
                size="sm"
              >
                编辑推荐位
              </Button>
            </div>
          </CardHeader>
        </Card>

        {/* 内容管理组件 */}
        <Card>
          <CardHeader>
            <CardTitle>内容管理</CardTitle>
            <CardDescription>管理与此推荐位关联的内容</CardDescription>
          </CardHeader>
          <CardContent>
            <FeatureContents featureId={params.id} />
          </CardContent>
        </Card>
      </Show>
    </div>
  );
}
