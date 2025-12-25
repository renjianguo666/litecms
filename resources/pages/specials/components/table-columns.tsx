import { Pencil, Trash2, List, ExternalLink } from "lucide-solid";
import { A } from "@solidjs/router";
import type { ColumnDef } from "@tanstack/solid-table";

import type { SpecialValues } from "@/lib/api";
import { special } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import type { TableMeta } from "@/components/datatable";
import { RequirePermission } from "@/components/require-permission";
import { toast } from "@/components/ui/toast";

export const columns: ColumnDef<SpecialValues>[] = [
  {
    accessorKey: "id",
    header: "ID",
    cell: (info) => {
      const id = info.getValue() as string;
      return (
        <Tooltip>
          <TooltipTrigger
            as="button"
            class="font-mono text-xs text-muted-foreground hover:text-foreground cursor-pointer"
            onClick={() => {
              navigator.clipboard.writeText(id);
              toast.success(id, "复制成功");
            }}
          >
            {id.slice(-8)}
          </TooltipTrigger>
          <TooltipContent>{id}</TooltipContent>
        </Tooltip>
      );
    },
  },
  {
    accessorKey: "name",
    header: "名称",
    cell: (info) => {
      const row = info.row.original;
      return (
        <a
          href={row.url}
          target="_blank"
          rel="noopener noreferrer"
          class="group inline-flex items-center gap-1 font-medium hover:opacity-70 transition-opacity"
        >
          <span>{info.getValue() as string}</span>
          <ExternalLink class="size-3.5 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
        </a>
      );
    },
  },
  {
    accessorKey: "is_active",
    header: "状态",
    cell: (info) => {
      const isActive = info.getValue() as boolean;
      return (
        <span
          class={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-md border ${isActive
            ? "bg-green-500/10 text-green-600 border-green-500/20 dark:text-green-400"
            : "bg-destructive/10 text-destructive border-destructive/20"
            }`}
        >
          {isActive ? "上线" : "下线"}
        </span>
      );
    },
  },
  {
    accessorKey: "priority",
    header: "优先级",
    cell: (info) => (
      <span class="text-sm text-muted-foreground">
        {info.getValue() as number}
      </span>
    ),
  },
  {
    accessorKey: "created_at",
    header: "创建时间",
    cell: (info) => {
      const date = new Date(info.getValue() as string);
      return (
        <span class="text-sm text-muted-foreground">
          {date.toLocaleDateString("zh-CN")}
        </span>
      );
    },
  },
  {
    id: "actions",
    header: "操作",
    cell: (info) => {
      const item = info.row.original;
      const meta = info.table.options.meta as TableMeta;

      const handleDelete = async () => {
        try {
          await special.delete(item.id);
          meta.refetch();
        } catch (error) {
          console.error("删除失败", error);
        }
      };

      return (
        <div class="flex items-center gap-1">
          <RequirePermission permission="taxonomies:view_special_content">
            <Tooltip>
              <TooltipTrigger
                as={(triggerProps: object) => (
                  <Button
                    as={A}
                    href={`/specials/${item.id}/contents`}
                    variant="ghost"
                    size="icon-sm"
                    {...triggerProps}
                  >
                    <List class="size-3.5" />
                  </Button>
                )}
              />
              <TooltipContent>内容管理</TooltipContent>
            </Tooltip>
          </RequirePermission>

          <RequirePermission permission="taxonomies:update_special">
            <Tooltip>
              <TooltipTrigger
                as={(triggerProps: object) => (
                  <Button
                    as={A}
                    href={`/specials/${item.id}`}
                    variant="ghost"
                    size="icon-sm"
                    {...triggerProps}
                  >
                    <Pencil class="size-3.5" />
                  </Button>
                )}
              />
              <TooltipContent>编辑</TooltipContent>
            </Tooltip>
          </RequirePermission>

          <RequirePermission permission="taxonomies:delete_special">
            <Dialog>
              <Tooltip>
                <DialogTrigger
                  as={(dialogProps: object) => (
                    <TooltipTrigger
                      as={Button}
                      variant="ghost"
                      size="icon-sm"
                      class="text-destructive hover:text-destructive hover:bg-destructive/10"
                      {...dialogProps}
                    >
                      <Trash2 class="size-3.5" />
                    </TooltipTrigger>
                  )}
                />
                <TooltipContent>删除</TooltipContent>
              </Tooltip>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>删除专题</DialogTitle>
                  <DialogDescription>
                    删除后将无法恢复，确定要删除该专题吗？
                  </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                  <DialogClose as={Button} variant="outline">
                    取消
                  </DialogClose>
                  <DialogClose
                    as={Button}
                    variant="destructive"
                    onClick={handleDelete}
                  >
                    确认删除
                  </DialogClose>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </RequirePermission>
        </div>
      );
    },
    enableHiding: false,
  },
];
