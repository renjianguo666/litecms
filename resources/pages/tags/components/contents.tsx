import { createSignal, createResource, For, Show } from "solid-js";
import { Trash2, Plus, Search, Loader } from "lucide-solid";

import { tag, article } from "@/lib/api";
import { toast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";

interface TagContentsProps {
  tagId: string;
}

export default function TagContents(props: TagContentsProps) {
  // 状态
  const [showAddModal, setShowAddModal] = createSignal(false);
  const [searchKeyword, setSearchKeyword] = createSignal("");
  const [selectedIds, setSelectedIds] = createSignal<Set<string>>(new Set());
  const [isAdding, setIsAdding] = createSignal(false);
  const [removeTarget, setRemoveTarget] = createSignal<{
    contentId: string;
    title: string;
  } | null>(null);
  const [isRemoving, setIsRemoving] = createSignal(false);

  // 获取标签文章列表
  const [contentsData, { refetch }] = createResource(
    () => props.tagId,
    (id) => tag.listContents(id),
  );

  // 搜索文章（用于添加）
  const [searchResults] = createResource(
    () => (showAddModal() ? searchKeyword() : null),
    async (keyword) => {
      if (!keyword || keyword.length < 2) return null;
      const result = await article.list({ search: keyword, page_size: 20 });
      return result.items;
    },
  );

  // 移除文章
  const handleRemove = async () => {
    const target = removeTarget();
    if (!target) return;

    setIsRemoving(true);
    try {
      await tag.removeContent(props.tagId, target.contentId);
      toast.success("移除成功");
      setRemoveTarget(null);
      refetch();
    } catch {
      toast.error("移除失败");
    } finally {
      setIsRemoving(false);
    }
  };

  // 切换选择
  const toggleSelect = (id: string) => {
    const newSet = new Set(selectedIds());
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    setSelectedIds(newSet);
  };

  // 全选/取消全选
  const toggleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(new Set<string>(searchResults()?.map((a) => a.id) ?? []));
    } else {
      setSelectedIds(new Set<string>());
    }
  };

  // 添加选中的文章
  const handleAddSelected = async () => {
    const ids = Array.from(selectedIds());
    if (ids.length === 0) {
      toast.error("请选择要添加的文章");
      return;
    }

    setIsAdding(true);
    try {
      const result = await tag.addContents(props.tagId, ids);
      toast.success(`成功添加 ${result.added} 篇文章`);
      closeModal();
      refetch();
    } catch {
      toast.error("添加失败");
    } finally {
      setIsAdding(false);
    }
  };

  // 关闭模态框
  const closeModal = () => {
    setShowAddModal(false);
    setSelectedIds(new Set<string>());
    setSearchKeyword("");
  };

  // 状态徽章渲染
  const renderStatusBadge = (status: string) => {
    switch (status) {
      case "published":
        return (
          <Badge class="bg-green-500/10 text-green-600 border-green-500/20 dark:text-green-400">
            已发布
          </Badge>
        );
      case "draft":
        return (
          <Badge class="bg-yellow-500/10 text-yellow-600 border-yellow-500/20 dark:text-yellow-400">
            草稿
          </Badge>
        );
      default:
        return <Badge variant="secondary">已归档</Badge>;
    }
  };

  return (
    <div class="space-y-4">
      {/* 工具栏 */}
      <div class="flex items-center justify-between">
        <div class="text-sm text-muted-foreground">
          共 {contentsData()?.contents?.length ?? 0} 篇文章
        </div>
        <Button size="sm" onClick={() => setShowAddModal(true)}>
          <Plus class="size-4" />
          添加文章
        </Button>
      </div>

      {/* 文章列表 */}
      <Show
        when={!contentsData.loading}
        fallback={
          <div class="flex justify-center py-8">
            <Loader class="size-6 animate-spin text-primary" />
          </div>
        }
      >
        <Show
          when={contentsData()?.contents?.length}
          fallback={
            <div class="text-center py-12 text-muted-foreground">
              <p class="text-lg mb-2">暂无文章</p>
              <p class="text-sm">点击「添加文章」将文章加入此标签</p>
            </div>
          }
        >
          <div class="rounded-lg border border-border overflow-hidden">
            <Table>
              <TableHeader class="bg-muted/50">
                <TableRow class="hover:bg-muted/50">
                  <TableHead class="px-4 font-semibold">标题</TableHead>
                  <TableHead class="px-4 font-semibold w-20">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <For each={contentsData()?.contents}>
                  {(content, index) => (
                    <TableRow class={index() % 2 === 1 ? "bg-muted/30" : ""}>
                      <TableCell class="px-4 py-3">
                        <span class="font-medium">{content.title}</span>
                      </TableCell>
                      <TableCell class="px-4 py-3">
                        <Tooltip>
                          <TooltipTrigger
                            as={(triggerProps: object) => (
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                class="text-destructive hover:text-destructive hover:bg-destructive/10"
                                onClick={() =>
                                  setRemoveTarget({
                                    contentId: content.content_id,
                                    title: content.title,
                                  })
                                }
                                {...triggerProps}
                              >
                                <Trash2 class="size-3.5" />
                              </Button>
                            )}
                          />
                          <TooltipContent>移除</TooltipContent>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  )}
                </For>
              </TableBody>
            </Table>
          </div>
        </Show>
      </Show>

      {/* 添加文章模态框 */}
      <Dialog open={showAddModal()} onOpenChange={setShowAddModal}>
        <DialogContent class="max-w-2xl">
          <DialogHeader>
            <DialogTitle>添加文章到标签</DialogTitle>
          </DialogHeader>

          {/* 搜索框 */}
          <div class="relative mb-4">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
            <Input
              type="text"
              placeholder="输入关键词搜索文章（至少2个字符）"
              class="pl-10"
              value={searchKeyword()}
              onInput={(e) => setSearchKeyword(e.currentTarget.value)}
            />
          </div>

          {/* 搜索结果 */}
          <div class="min-h-[300px] max-h-[400px] overflow-y-auto border border-border rounded-lg">
            <Show
              when={searchKeyword().length >= 2}
              fallback={
                <div class="flex items-center justify-center h-[300px] text-muted-foreground">
                  请输入关键词搜索文章
                </div>
              }
            >
              <Show
                when={!searchResults.loading}
                fallback={
                  <div class="flex items-center justify-center h-[300px]">
                    <Loader class="size-6 animate-spin text-primary" />
                  </div>
                }
              >
                <Show
                  when={searchResults()?.length}
                  fallback={
                    <div class="flex items-center justify-center h-[300px] text-muted-foreground">
                      未找到相关文章
                    </div>
                  }
                >
                  <Table>
                    <TableHeader class="bg-muted/50">
                      <TableRow class="hover:bg-muted/50">
                        <TableHead class="px-4 font-semibold w-8">
                          <Checkbox
                            checked={
                              searchResults()?.length === selectedIds().size &&
                              selectedIds().size > 0
                            }
                            onChange={toggleSelectAll}
                          />
                        </TableHead>
                        <TableHead class="px-4 font-semibold">标题</TableHead>
                        <TableHead class="px-4 font-semibold w-24">
                          状态
                        </TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <For each={searchResults()}>
                        {(item, index) => (
                          <TableRow
                            class={`cursor-pointer ${index() % 2 === 1 ? "bg-muted/30" : ""}`}
                            onClick={() => toggleSelect(item.id)}
                          >
                            <TableCell class="px-4 py-3">
                              <Checkbox
                                checked={selectedIds().has(item.id)}
                                onChange={() => toggleSelect(item.id)}
                              />
                            </TableCell>
                            <TableCell class="px-4 py-3">
                              <span class="font-medium">{item.title}</span>
                            </TableCell>
                            <TableCell class="px-4 py-3">
                              {renderStatusBadge(item.status)}
                            </TableCell>
                          </TableRow>
                        )}
                      </For>
                    </TableBody>
                  </Table>
                </Show>
              </Show>
            </Show>
          </div>

          {/* 已选择提示 */}
          <Show when={selectedIds().size > 0}>
            <div class="text-sm text-muted-foreground">
              已选择 {selectedIds().size} 篇文章
            </div>
          </Show>

          <DialogFooter>
            <Button variant="outline" onClick={closeModal}>
              取消
            </Button>
            <Button
              disabled={selectedIds().size === 0 || isAdding()}
              onClick={handleAddSelected}
            >
              {isAdding() && <Loader class="size-4 animate-spin" />}
              添加 {selectedIds().size} 篇文章
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* 移除确认对话框 */}
      <Dialog
        open={removeTarget() !== null}
        onOpenChange={(open) => !open && setRemoveTarget(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>移除文章</DialogTitle>
            <DialogDescription>
              确定要从标签中移除「{removeTarget()?.title}」吗？
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose as={Button} variant="outline">
              取消
            </DialogClose>
            <Button
              variant="destructive"
              onClick={handleRemove}
              disabled={isRemoving()}
            >
              {isRemoving() ? "移除中..." : "确认移除"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
