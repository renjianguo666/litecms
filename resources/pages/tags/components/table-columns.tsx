import { Pencil, Trash2, List, ExternalLink } from "lucide-solid";
import { A } from "@solidjs/router";
import type { ColumnDef } from "@tanstack/solid-table";

import type { TagValues } from "@/lib/api";
import { tag } from "@/lib/api";
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

export const columns: ColumnDef<TagValues>[] = [
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
    accessorKey: "updated_at",
    header: "更新时间",
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
          await tag.delete(item.id);
          meta.refetch();
        } catch (error) {
          console.error("删除失败", error);
        }
      };

      return (
        <div class="flex items-center gap-1">
          <RequirePermission permission="taxonomies:view_tag_content">
            <Tooltip>
              <TooltipTrigger
                as={(triggerProps: object) => (
                  <Button
                    as={A}
                    href={`/tags/${item.id}/contents`}
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

          <RequirePermission permission="taxonomies:update_tag">
            <Tooltip>
              <TooltipTrigger
                as={(triggerProps: object) => (
                  <Button
                    as={A}
                    href={`/tags/${item.id}`}
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

          <RequirePermission permission="taxonomies:delete_tag">
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
                  <DialogTitle>删除标签</DialogTitle>
                  <DialogDescription>
                    删除后将无法恢复，确定要删除该标签吗？
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
