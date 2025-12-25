import { A } from "@solidjs/router";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowUpRight } from "lucide-solid";

export default function DashboardIndex() {
  return (
    <div class="space-y-6">

      {/* Recent Content & Quick Actions */}
      <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        {/* Recent Articles */}
        <Card class="col-span-4">
          <CardHeader>
            <div class="flex items-center justify-between">
              <div>
                <CardTitle>最近文章</CardTitle>
                <CardDescription class="mt-1.5">
                  最新发布和编辑的文章
                </CardDescription>
              </div>
              <Button as={A} href="/articles" variant="ghost" size="sm">
                查看全部
                <ArrowUpRight class="ml-1 h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div class="space-y-6">
              <div class="flex items-start justify-between space-x-4">
                <div class="space-y-1">
                  <p class="text-sm font-medium leading-none">
                    欢迎使用 LiteCMS
                  </p>
                  <p class="text-xs text-muted-foreground">2025-01-01</p>
                </div>
                <Badge class="shrink-0 bg-green-500/10 text-green-600 border-green-500/20 dark:text-green-400">
                  已发布
                </Badge>
              </div>

              <div class="flex items-start justify-between space-x-4">
                <div class="space-y-1">
                  <p class="text-sm font-medium leading-none">系统使用指南</p>
                  <p class="text-xs text-muted-foreground">2025-01-01</p>
                </div>
                <Badge class="shrink-0 bg-green-500/10 text-green-600 border-green-500/20 dark:text-green-400">
                  已发布
                </Badge>
              </div>

              <div class="flex items-start justify-between space-x-4">
                <div class="space-y-1">
                  <p class="text-sm font-medium leading-none">新功能预告</p>
                  <p class="text-xs text-muted-foreground">2025-01-02</p>
                </div>
                <Badge class="shrink-0 bg-yellow-500/10 text-yellow-600 border-yellow-500/20 dark:text-yellow-400">
                  草稿
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card class="col-span-3">
          <CardHeader>
            <CardTitle>快捷操作</CardTitle>
            <CardDescription class="mt-1.5">快速创建和管理内容</CardDescription>
          </CardHeader>
          <CardContent class="space-y-2">
            <Button
              as={A}
              href="/articles/create"
              variant="outline"
              class="w-full justify-start"
            >
              新建文章
            </Button>
            <Button
              as={A}
              href="/categories/create"
              variant="outline"
              class="w-full justify-start"
            >
              新建栏目
            </Button>
            <Button
              as={A}
              href="/specials/create"
              variant="outline"
              class="w-full justify-start"
            >
              新建专题
            </Button>
            <Button
              as={A}
              href="/tags/create"
              variant="outline"
              class="w-full justify-start"
            >
              新建标签
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
