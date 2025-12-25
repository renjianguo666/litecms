import { Pencil, Trash2 } from "lucide-solid";
import { A } from "@solidjs/router";
import type { ColumnDef } from "@tanstack/solid-table";

import type { UserLiteValues } from "@/lib/api";
import { user } from "@/lib/api";
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

export const columns: ColumnDef<UserLiteValues>[] = [
  {
    accessorKey: "username",
    header: "用户名",
    cell: (info) => (
      <span class="font-medium">{info.getValue() as string}</span>
    ),
  },
  {
    accessorKey: "email",
    header: "邮箱",
    cell: (info) => {
      const email = info.getValue() as string | null;
      return email ? (
        <span class="text-sm">{email}</span>
      ) : (
        <span class="text-sm text-muted-foreground">-</span>
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
          class={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${isActive
              ? "bg-primary/10 text-primary"
              : "bg-muted text-muted-foreground"
            }`}
        >
          {isActive ? "启用" : "禁用"}
        </span>
      );
    },
  },
  {
    accessorKey: "is_superuser",
    header: "超级管理员",
    cell: (info) => {
      const isSuperuser = info.getValue() as boolean;
      return (
        <span
          class={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${isSuperuser
              ? "bg-secondary text-secondary-foreground"
              : "bg-muted text-muted-foreground"
            }`}
        >
          {isSuperuser ? "是" : "否"}
        </span>
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
    id: "actions",
    header: "操作",
    cell: (info) => {
      const row = info.row.original;
      const meta = info.table.options.meta as TableMeta;

      const handleDelete = async () => {
        try {
          await user.delete(row.id);
          meta.refetch();
        } catch (error) {
          console.error("删除失败", error);
        }
      };

      return (
        <div class="flex items-center gap-1">
          <RequirePermission permission="accounts:update_user">
            <Tooltip>
              <TooltipTrigger
                as={(triggerProps: object) => (
                  <Button
                    as={A}
                    href={`/users/${row.id}`}
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

          <RequirePermission permission="accounts:delete_user">
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
                  <DialogTitle>删除用户</DialogTitle>
                  <DialogDescription>
                    删除后将无法恢复，确定要删除该用户吗？
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
