import { Pencil, Trash2 } from "lucide-solid";
import { A } from "@solidjs/router";
import type { ColumnDef } from "@tanstack/solid-table";

import type { RoleLiteValues } from "@/lib/api";
import { role } from "@/lib/api";
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

export const columns: ColumnDef<RoleLiteValues>[] = [
  {
    accessorKey: "name",
    header: "角色名称",
    cell: (info) => (
      <span class="font-medium">{info.getValue() as string}</span>
    ),
  },
  {
    accessorKey: "description",
    header: "描述",
    cell: (info) => {
      const description = info.getValue() as string | null;
      return description ? (
        <span class="text-sm">{description}</span>
      ) : (
        <span class="text-sm text-muted-foreground">-</span>
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
          await role.delete(row.id);
          meta.refetch();
        } catch (error) {
          console.error("删除失败", error);
        }
      };

      return (
        <div class="flex items-center gap-1">
          <RequirePermission permission="accounts:update_role">
            <Tooltip>
              <TooltipTrigger
                as={(triggerProps: object) => (
                  <Button
                    as={A}
                    href={`/roles/${row.id}`}
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

          <RequirePermission permission="accounts:delete_role">
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
                  <DialogTitle>删除角色</DialogTitle>
                  <DialogDescription>
                    删除后将无法恢复，确定要删除该角色吗？
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
