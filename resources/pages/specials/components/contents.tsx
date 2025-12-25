import { createSignal, createResource, For, Show } from "solid-js";
import { Trash2, Plus, GripVertical, Search, Loader } from "lucide-solid";

import { special, article } from "@/lib/api";
import { toast } from "@/components/ui/toast";
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
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";

interface SpecialContentsProps {
  specialId: string;
}

export default function SpecialContents(props: SpecialContentsProps) {
  // 状态
  const [showAddModal, setShowAddModal] = createSignal(false);
  const [searchKeyword, setSearchKeyword] = createSignal("");
  const [selectedIds, setSelectedIds] = createSignal<Set<string>>(new Set());
  const [isAdding, setIsAdding] = createSignal(false);

  // 获取专题文章列表
  const [contentsData, { refetch }] = createResource(
    () => props.specialId,
    (id) => special.listContents(id),
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
  const handleRemove = async (contentId: string) => {
    try {
      await special.removeContent(props.specialId, contentId);
      toast.success("移除成功");
      refetch();
    } catch {
      toast.error("移除失败");
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
      const result = await special.addContents(props.specialId, ids);
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

  // 格式化日期
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("zh-CN");
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
              <p class="text-sm">点击「添加文章」将文章加入此专题</p>
            </div>
          }
        >
          <div class="rounded-lg border border-border overflow-hidden">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-border bg-muted/50">
                  <th class="h-10 px-4 text-left align-middle font-semibold text-muted-foreground w-8"></th>
                  <th class="h-10 px-4 text-left align-middle font-semibold text-muted-foreground">
                    标题
                  </th>
                  <th class="h-10 px-4 text-left align-middle font-semibold text-muted-foreground w-32">
                    添加时间
                  </th>
                  <th class="h-10 px-4 text-left align-middle font-semibold text-muted-foreground w-20">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody>
                <For each={contentsData()?.contents}>
                  {(content, index) => (
                    <tr
                      class={`border-b border-border transition-colors hover:bg-muted/50 ${index() % 2 === 1 ? "bg-muted/30" : ""
                        }`}
                    >
                      <td class="h-12 px-4 align-middle">
                        <GripVertical class="size-4 text-foreground/30 cursor-grab" />
                      </td>
                      <td class="h-12 px-4 align-middle">
                        <span class="font-medium">{content.title}</span>
                        <Show when={content.headline}>
                          <span class="ml-2 inline-flex items-center px-1.5 py-0.5 text-xs font-medium rounded bg-primary/10 text-primary">
                            头条
                          </span>
                        </Show>
                      </td>
                      <td class="h-12 px-4 align-middle text-muted-foreground">
                        {formatDate(content.added_at)}
                      </td>
                      <td class="h-12 px-4 align-middle">
                        <Dialog>
                          <Tooltip>
                            <TooltipTrigger
                              as={(triggerProps: object) => (
                                <DialogTrigger
                                  as={(dialogProps: object) => (
                                    <Button
                                      variant="ghost"
                                      size="icon-sm"
                                      class="text-destructive hover:text-destructive hover:bg-destructive/10"
                                      {...triggerProps}
                                      {...dialogProps}
                                    >
                                      <Trash2 class="size-3.5" />
                                    </Button>
                                  )}
                                />
                              )}
                            />
                            <TooltipContent>移除</TooltipContent>
                          </Tooltip>
                          <DialogContent>
                            <DialogHeader>
                              <DialogTitle>移除文章</DialogTitle>
                              <DialogDescription>
                                确定要从专题中移除「{content.title}」吗？
                              </DialogDescription>
                            </DialogHeader>
                            <DialogFooter>
                              <DialogClose as={Button} variant="outline">
                                取消
                              </DialogClose>
                              <DialogClose
                                as={Button}
                                variant="destructive"
                                onClick={() => handleRemove(content.content_id)}
                              >
                                确认移除
                              </DialogClose>
                            </DialogFooter>
                          </DialogContent>
                        </Dialog>
                      </td>
                    </tr>
                  )}
                </For>
              </tbody>
            </table>
          </div>
        </Show>
      </Show>

      {/* 添加文章模态框 */}
      <Dialog open={showAddModal()} onOpenChange={setShowAddModal}>
        <DialogContent class="max-w-2xl">
          <DialogHeader>
            <DialogTitle>添加文章到专题</DialogTitle>
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
                  <table class="w-full text-sm">
                    <thead>
                      <tr class="border-b border-border bg-muted/50">
                        <th class="h-10 px-4 text-left align-middle font-semibold text-muted-foreground w-8">
                          <Checkbox
                            checked={
                              searchResults()?.length === selectedIds().size &&
                              selectedIds().size > 0
                            }
                            onChange={toggleSelectAll}
                          />
                        </th>
                        <th class="h-10 px-4 text-left align-middle font-semibold text-muted-foreground">
                          标题
                        </th>
                        <th class="h-10 px-4 text-left align-middle font-semibold text-muted-foreground w-24">
                          状态
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      <For each={searchResults()}>
                        {(item, index) => (
                          <tr
                            class={`border-b border-border transition-colors hover:bg-muted/50 cursor-pointer ${index() % 2 === 1 ? "bg-muted/30" : ""
                              }`}
                            onClick={() => toggleSelect(item.id)}
                          >
                            <td class="h-12 px-4 align-middle">
                              <Checkbox
                                checked={selectedIds().has(item.id)}
                                onChange={() => toggleSelect(item.id)}
                              />
                            </td>
                            <td class="h-12 px-4 align-middle">
                              <span class="font-medium">{item.title}</span>
                            </td>
                            <td class="h-12 px-4 align-middle">
                              <span
                                class={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-md border ${item.status === "published"
                                  ? "bg-green-500/10 text-green-600 border-green-500/20 dark:text-green-400"
                                  : item.status === "draft"
                                    ? "bg-yellow-500/10 text-yellow-600 border-yellow-500/20 dark:text-yellow-400"
                                    : "bg-muted text-muted-foreground border-border"
                                  }`}
                              >
                                {item.status === "published"
                                  ? "已发布"
                                  : item.status === "draft"
                                    ? "草稿"
                                    : "已归档"}
                              </span>
                            </td>
                          </tr>
                        )}
                      </For>
                    </tbody>
                  </table>
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
    </div>
  );
}
