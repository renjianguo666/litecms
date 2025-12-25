import { splitProps, type JSX, For } from "solid-js";
import { cn } from "@/lib/utils";

type SkeletonProps = JSX.HTMLAttributes<HTMLDivElement>;

function Skeleton(props: SkeletonProps) {
  const [local, others] = splitProps(props, ["class"]);

  return (
    <div
      data-slot="skeleton"
      class={cn("bg-muted animate-pulse rounded-md", local.class)}
      {...others}
    />
  );
}

/**
 * 卡片骨架屏
 */
function CardSkeleton() {
  return (
    <div class="rounded-lg border bg-card p-6 space-y-4">
      <div class="space-y-2">
        <Skeleton class="h-5 w-1/3" />
        <Skeleton class="h-4 w-1/2" />
      </div>
      <div class="space-y-2">
        <Skeleton class="h-4 w-full" />
        <Skeleton class="h-4 w-full" />
        <Skeleton class="h-4 w-2/3" />
      </div>
    </div>
  );
}

/**
 * 表格骨架屏
 */
function TableSkeleton(props: { rows?: number }) {
  const rows = () => props.rows ?? 5;
  return (
    <div class="rounded-lg border">
      {/* 表头 */}
      <div class="border-b bg-muted/50 p-4">
        <div class="flex gap-4">
          <Skeleton class="h-4 w-1/4" />
          <Skeleton class="h-4 w-1/4" />
          <Skeleton class="h-4 w-1/4" />
          <Skeleton class="h-4 w-1/4" />
        </div>
      </div>
      {/* 表格行 */}
      <For each={Array.from({ length: rows() })}>
        {() => (
          <div class="border-b last:border-0 p-4">
            <div class="flex gap-4">
              <Skeleton class="h-4 w-1/4" />
              <Skeleton class="h-4 w-1/4" />
              <Skeleton class="h-4 w-1/4" />
              <Skeleton class="h-4 w-1/4" />
            </div>
          </div>
        )}
      </For>
    </div>
  );
}

/**
 * 表单骨架屏
 */
function FormSkeleton() {
  return (
    <div class="space-y-6">
      {/* 表单字段 */}
      <For each={Array.from({ length: 4 })}>
        {() => (
          <div class="space-y-2">
            <Skeleton class="h-4 w-20" />
            <Skeleton class="h-10 w-full" />
          </div>
        )}
      </For>
      {/* 提交按钮 */}
      <Skeleton class="h-10 w-24" />
    </div>
  );
}

/**
 * 页面内容骨架屏（通用）
 */
function PageSkeleton() {
  return (
    <div class="space-y-6">
      {/* 页面标题区域 */}
      <div class="flex items-center justify-between">
        <div class="space-y-1">
          <Skeleton class="h-8 w-48" />
          <Skeleton class="h-4 w-64" />
        </div>
        <Skeleton class="h-10 w-24" />
      </div>
      {/* 内容区域 */}
      <CardSkeleton />
    </div>
  );
}

export { Skeleton, CardSkeleton, TableSkeleton, FormSkeleton, PageSkeleton };
export type { SkeletonProps };

