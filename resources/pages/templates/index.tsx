import {
  createSignal,
  createResource,
  createEffect,
  Show,
  For,
} from "solid-js";
import { useParams, useNavigate } from "@solidjs/router";
import {
  Plus,
  Trash2,
  RefreshCw,
  FileCode,
  Loader,
  Pencil,
  FolderOpen,
} from "lucide-solid";

import { template } from "@/lib/api";
import { toast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import {
  ContextMenu,
  ContextMenuTrigger,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
} from "@/components/ui/context-menu";
import CodeEditor from "./components/code-editor";

export default function Templates() {
  const params = useParams<{ path?: string }>();
  const navigate = useNavigate();

  const [content, setContent] = createSignal("");
  const [originalContent, setOriginalContent] = createSignal("");
  const [isLoading, setIsLoading] = createSignal(false);
  const [showNewFileModal, setShowNewFileModal] = createSignal(false);
  const [newFileName, setNewFileName] = createSignal("");
  const [showRenameModal, setShowRenameModal] = createSignal(false);
  const [renamePath, setRenamePath] = createSignal<string | null>(null);
  const [renameFileName, setRenameFileName] = createSignal("");

  // 确认对话框状态
  const [deleteTargetPath, setDeleteTargetPath] = createSignal<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = createSignal(false);
  const [showUnsavedDialog, setShowUnsavedDialog] = createSignal(false);
  const [pendingAction, setPendingAction] = createSignal<(() => void) | null>(null);

  let newFileInputRef: HTMLInputElement | undefined;
  let renameInputRef: HTMLInputElement | undefined;

  // 选中的文件（直接从 URL 参数获取）
  const selectedPath = () => (params.path ? decodeURIComponent(params.path) : null);

  // 文件列表（直接返回 string[]）
  const [files, { refetch }] = createResource(() => template.list());

  const refreshList = () => {
    refetch();
  };

  const hasChanges = () => content() !== originalContent();

  const loadFile = async (path: string) => {
    setIsLoading(true);
    try {
      const file = await template.get(path);
      setContent(file.content);
      setOriginalContent(file.content);
    } catch {
      toast.error("加载文件失败");
      navigate("/templates");
    } finally {
      setIsLoading(false);
    }
  };

  const navigateToFile = (path: string) => {
    navigate(`/templates/${encodeURIComponent(path)}`);
  };

  const navigateToList = () => {
    navigate("/templates");
  };

  createEffect(() => {
    const path = selectedPath();
    if (path) {
      loadFile(path);
    } else {
      setContent("");
      setOriginalContent("");
    }
  });

  const handleSelectFile = (path: string) => {
    if (selectedPath() === path) return;

    if (hasChanges()) {
      setPendingAction(() => () => navigateToFile(path));
      setShowUnsavedDialog(true);
      return;
    }

    navigateToFile(path);
  };

  const confirmUnsavedAction = () => {
    const action = pendingAction();
    if (action) action();
    setShowUnsavedDialog(false);
    setPendingAction(null);
  };

  const cancelUnsavedAction = () => {
    setShowUnsavedDialog(false);
    setPendingAction(null);
  };

  const handleSave = async () => {
    const path = selectedPath();
    if (!path) return;

    setIsLoading(true);
    try {
      await template.save(path, content());
      setOriginalContent(content());
      toast.success("保存成功");
    } catch {
      toast.error("保存失败");
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenDelete = (path: string) => {
    setDeleteTargetPath(path);
    setShowDeleteDialog(true);
  };

  const confirmDelete = async () => {
    const path = deleteTargetPath();
    if (!path) return;

    setIsLoading(true);
    try {
      await template.delete(path);
      setShowDeleteDialog(false);
      setDeleteTargetPath(null);

      if (selectedPath() === path) {
        navigateToList();
        setContent("");
        setOriginalContent("");
      }

      refreshList();
      toast.success("删除成功");
    } catch {
      toast.error("删除失败");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateFile = async () => {
    let fileName = newFileName().trim();
    if (!fileName) {
      toast.error("请输入文件名");
      return;
    }

    if (!fileName.endsWith(".html")) {
      fileName = `${fileName}.html`;
    }

    setIsLoading(true);
    try {
      await template.save(fileName, "");
      setShowNewFileModal(false);
      setNewFileName("");
      refreshList();
      navigateToFile(fileName);
      toast.success("创建成功");
    } catch {
      toast.error("创建失败");
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenRename = (path: string) => {
    setRenamePath(path);
    const fileName = path.split("/").pop() || "";
    setRenameFileName(fileName);
    setShowRenameModal(true);

    setTimeout(() => {
      if (renameInputRef) {
        renameInputRef.focus();
        const dotIndex = fileName.lastIndexOf(".");
        if (dotIndex > 0) {
          renameInputRef.setSelectionRange(0, dotIndex);
        } else {
          renameInputRef.select();
        }
      }
    }, 0);
  };

  const handleRename = async () => {
    const path = renamePath();
    const name = renameFileName().trim();

    if (!path || !name) {
      toast.error("请输入新文件名");
      return;
    }

    if (!name.endsWith(".html")) {
      toast.error("文件名必须以 .html 结尾");
      return;
    }

    setIsLoading(true);
    try {
      await template.rename(path, name);
      setShowRenameModal(false);
      setRenamePath(null);
      setRenameFileName("");
      refreshList();

      if (selectedPath() === path) {
        const dir = path.split("/").slice(0, -1).join("/");
        const newPath = dir ? `${dir}/${name}` : name;
        navigateToFile(newPath);
      }

      toast.success("重命名成功");
    } catch {
      toast.error("重命名失败");
    } finally {
      setIsLoading(false);
    }
  };

  const closeNewFileModal = () => {
    setShowNewFileModal(false);
    setNewFileName("");
  };

  const closeRenameModal = () => {
    setShowRenameModal(false);
    setRenamePath(null);
    setRenameFileName("");
  };

  return (
    <div class="h-[calc(100vh-8rem)]">
      {/* 顶部操作栏 */}
      <div class="flex items-center justify-between mb-4">
        <div class="text-sm text-muted-foreground">
          模板文件管理
          <Show when={selectedPath()}>
            <span class="ml-4 text-foreground">
              当前编辑:{" "}
              <code class="bg-muted px-1.5 py-0.5 rounded text-xs">
                {selectedPath()}
              </code>
              {hasChanges() && <span class="text-warning ml-1">*</span>}
            </span>
          </Show>
        </div>

        <div class="flex items-center gap-2">
          <Button
            variant="default"
            size="sm"
            onClick={() => {
              setShowNewFileModal(true);
              setTimeout(() => newFileInputRef?.focus(), 0);
            }}
          >
            <Plus class="size-4" />
            新建模板
          </Button>
          <Button variant="ghost" size="sm" onClick={refreshList}>
            <RefreshCw class="size-4" />
            刷新
          </Button>
        </div>
      </div>

      {/* 主内容区 */}
      <div class="flex gap-4 h-[calc(100%-3rem)]">
        {/* 文件列表 */}
        <div class="w-64 shrink-0 bg-card rounded-lg border border-border overflow-auto">
          <div class="px-3 py-2 border-b border-border flex items-center gap-2">
            <FolderOpen class="size-4 text-warning" />
            <span class="font-medium text-sm">templates/</span>
          </div>

          <Show
            when={!files.loading}
            fallback={
              <div class="flex items-center justify-center py-8">
                <Loader class="size-5 animate-spin text-primary" />
              </div>
            }
          >
            <div class="py-2">
              <Show
                when={(files() ?? []).length > 0}
                fallback={
                  <div class="text-center text-muted-foreground py-8 text-sm">
                    暂无模板文件
                  </div>
                }
              >
                <For each={files() ?? []}>
                  {(file) => (
                    <ContextMenu>
                      <ContextMenuTrigger
                        as="div"
                        class={`group flex items-center gap-2 px-3 py-2 cursor-pointer transition-colors hover:bg-muted ${selectedPath() === file
                          ? "bg-primary/10 text-primary"
                          : ""
                          }`}
                        onClick={() => handleSelectFile(file)}
                      >
                        <FileCode class="size-4 shrink-0 text-muted-foreground" />
                        <span class="text-sm truncate flex-1">{file}</span>
                      </ContextMenuTrigger>
                      <ContextMenuContent>
                        <ContextMenuItem
                          class="gap-2"
                          onSelect={() => handleOpenRename(file)}
                        >
                          <Pencil class="size-4" />
                          重命名
                        </ContextMenuItem>
                        <ContextMenuSeparator />
                        <ContextMenuItem
                          class="gap-2"
                          variant="destructive"
                          onSelect={() => handleOpenDelete(file)}
                        >
                          <Trash2 class="size-4" />
                          删除
                        </ContextMenuItem>
                      </ContextMenuContent>
                    </ContextMenu>
                  )}
                </For>
              </Show>
            </div>
          </Show>
        </div>

        {/* 编辑器 */}
        <div class="flex-1 min-w-0 flex flex-col">
          <div class="flex-1">
            <Show
              when={selectedPath()}
              fallback={
                <div class="h-full flex items-center justify-center bg-card rounded-lg border border-border">
                  <div class="text-center text-muted-foreground">
                    <FileCode class="size-12 mx-auto mb-3 opacity-30" />
                    <p class="text-lg mb-2">选择一个模板文件开始编辑</p>
                    <p class="text-sm">或点击「新建模板」创建新文件</p>
                  </div>
                </div>
              }
            >
              <Show
                when={!isLoading()}
                fallback={
                  <div class="h-full flex items-center justify-center bg-card rounded-lg border border-border">
                    <Loader class="size-8 animate-spin text-primary" />
                  </div>
                }
              >
                <CodeEditor
                  value={content()}
                  onChange={setContent}
                  onSave={handleSave}
                />
              </Show>
            </Show>
          </div>
        </div>
      </div>

      {/* 新建文件模态框 */}
      <Dialog open={showNewFileModal()} onOpenChange={setShowNewFileModal}>
        <DialogContent class="max-w-md">
          <DialogHeader>
            <DialogTitle>新建模板文件</DialogTitle>
            <DialogDescription class="sr-only">
              创建新的模板文件
            </DialogDescription>
          </DialogHeader>

          <div class="flex flex-col gap-1.5">
            <Label for="new-file-name">文件名</Label>
            <Input
              ref={newFileInputRef}
              id="new-file-name"
              type="text"
              placeholder="例如: red.category.html"
              value={newFileName()}
              onInput={(e) => setNewFileName(e.currentTarget.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleCreateFile();
                else if (e.key === "Escape") closeNewFileModal();
              }}
            />
            <span class="text-xs text-muted-foreground">
              命名格式：{"{name}.{type}.html"}，如 red.category.html、tech.tag.html
            </span>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={closeNewFileModal}>
              取消
            </Button>
            <Button
              variant="default"
              onClick={handleCreateFile}
              disabled={isLoading() || !newFileName().trim()}
            >
              <Show when={isLoading()}>
                <Loader class="size-4 animate-spin" />
              </Show>
              创建
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 重命名模态框 */}
      <Dialog open={showRenameModal()} onOpenChange={setShowRenameModal}>
        <DialogContent class="max-w-md">
          <DialogHeader>
            <DialogTitle>重命名模板文件</DialogTitle>
            <DialogDescription class="sr-only">
              修改模板文件的名称
            </DialogDescription>
          </DialogHeader>

          <div class="flex flex-col gap-1.5">
            <Label for="rename-file-name">新文件名</Label>
            <Input
              ref={renameInputRef}
              id="rename-file-name"
              type="text"
              placeholder="例如: blue.category.html"
              value={renameFileName()}
              onInput={(e) => setRenameFileName(e.currentTarget.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleRename();
                else if (e.key === "Escape") closeRenameModal();
              }}
            />
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={closeRenameModal}>
              取消
            </Button>
            <Button
              variant="default"
              onClick={handleRename}
              disabled={isLoading() || !renameFileName().trim()}
            >
              <Show when={isLoading()}>
                <Loader class="size-4 animate-spin" />
              </Show>
              确定
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除确认对话框 */}
      <Dialog open={showDeleteDialog()} onOpenChange={setShowDeleteDialog}>
        <DialogContent showCloseButton={false}>
          <DialogHeader>
            <DialogTitle>删除模板</DialogTitle>
            <DialogDescription>
              删除后将无法恢复，确定要删除该模板吗？
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose as={Button} variant="outline">
              取消
            </DialogClose>
            <Button
              variant="destructive"
              onClick={confirmDelete}
              disabled={isLoading()}
            >
              {isLoading() ? "删除中..." : "确认删除"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 未保存更改确认对话框 */}
      <Dialog open={showUnsavedDialog()} onOpenChange={setShowUnsavedDialog}>
        <DialogContent showCloseButton={false}>
          <DialogHeader>
            <DialogTitle>未保存的更改</DialogTitle>
            <DialogDescription>
              当前文件有未保存的更改，是否放弃？
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={cancelUnsavedAction}>
              取消
            </Button>
            <Button variant="default" onClick={confirmUnsavedAction}>
              放弃更改
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
