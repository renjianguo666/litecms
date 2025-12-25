import { createSignal, Show, type Accessor } from "solid-js";
import type { Editor } from "@tiptap/core";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { validateAndSanitizeUrl } from "../utils/security";
import { inputClass } from "../utils/styles";

/**
 * 链接对话框属性
 */
export interface LinkDialogProps {
  /** 是否打开 */
  open: boolean;
  /** 关闭回调 */
  onClose: () => void;
  /** 编辑器实例 */
  editor: Accessor<Editor | null>;
}

/**
 * 链接对话框组件
 *
 * 用于插入或编辑超链接。
 */
export function LinkDialog(props: LinkDialogProps) {
  const [linkUrl, setLinkUrl] = createSignal("");
  const [linkText, setLinkText] = createSignal("");

  // 对话框打开时初始化状态
  const handleOpenChange = (open: boolean) => {
    if (open) {
      const ed = props.editor();
      if (ed) {
        const { href } = ed.getAttributes("link");
        const { from, to } = ed.state.selection;
        const text = ed.state.doc.textBetween(from, to, "");
        setLinkUrl(href || "");
        setLinkText(text);
      }
    } else {
      props.onClose();
    }
  };

  // 插入链接
  const insertLink = () => {
    const ed = props.editor();
    if (!ed) return;

    const url = linkUrl();
    const text = linkText();
    const sanitizedUrl = validateAndSanitizeUrl(url);

    if (!sanitizedUrl) {
      alert("请输入有效的 URL");
      return;
    }

    if (text) {
      ed.chain()
        .focus()
        .insertContent(`<a href="${sanitizedUrl}">${text}</a>`)
        .run();
    } else {
      ed.chain().focus().setLink({ href: sanitizedUrl }).run();
    }

    props.onClose();
  };

  // 移除链接
  const removeLink = () => {
    const ed = props.editor();
    if (!ed) return;
    ed.chain().focus().unsetLink().run();
    props.onClose();
  };

  return (
    <Dialog open={props.open} onOpenChange={handleOpenChange}>
      <DialogContent class="max-w-md z-1001">
        <DialogHeader>
          <DialogTitle>插入链接</DialogTitle>
        </DialogHeader>
        <div class="space-y-4 py-4">
          <div class="space-y-2">
            <label class="text-sm font-medium" for="editor-link-url">
              链接地址
            </label>
            <input
              id="editor-link-url"
              name="editor-link-url"
              type="url"
              class={inputClass}
              placeholder="https://example.com"
              value={linkUrl()}
              onInput={(e) => setLinkUrl(e.currentTarget.value)}
            />
          </div>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <label class="text-sm font-medium" for="editor-link-text">
                链接文本
              </label>
              <span class="text-xs text-muted-foreground">可选</span>
            </div>
            <input
              id="editor-link-text"
              name="editor-link-text"
              type="text"
              class={inputClass}
              placeholder="显示文本"
              value={linkText()}
              onInput={(e) => setLinkText(e.currentTarget.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Show when={props.editor()?.isActive("link")}>
            <Button variant="destructive" onClick={removeLink}>
              移除链接
            </Button>
          </Show>
          <div class="flex-1" />
          <Button variant="secondary" onClick={props.onClose}>
            取消
          </Button>
          <Button disabled={!linkUrl()} onClick={insertLink}>
            确定
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default LinkDialog;
