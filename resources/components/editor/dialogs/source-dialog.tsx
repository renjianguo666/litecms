import { createSignal, createEffect, type Accessor } from "solid-js";
import type { Editor } from "@tiptap/core";
import {
  Dialog,
  DialogOverlay,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { textareaClass } from "../utils/styles";

/**
 * 源代码对话框属性
 */
export interface SourceDialogProps {
  /** 是否打开 */
  open: boolean;
  /** 关闭回调 */
  onClose: () => void;
  /** 编辑器实例 */
  editor: Accessor<Editor | null>;
}

/**
 * 源代码对话框组件
 *
 * 用于查看和编辑 HTML 源代码。
 */
export function SourceDialog(props: SourceDialogProps) {
  const [sourceHtml, setSourceHtml] = createSignal("");

  createEffect(() => {
    if (props.open) {
      const ed = props.editor();
      if (ed) {
        setSourceHtml(ed.getHTML());
      }
    }
  });

  // 应用源代码
  const applySource = () => {
    const ed = props.editor();
    if (!ed) return;

    ed.chain().focus().setContent(sourceHtml()).run();
    props.onClose();
  };

  return (
    <Dialog open={props.open} onOpenChange={(open) => !open && props.onClose()}>
      <DialogOverlay />
      <DialogContent
        onPointerDownOutside={(e) => e.preventDefault()}
        class="sm:max-w-[60vw] h-[80vh] flex flex-col z-1001"
      >
        <DialogHeader>
          <DialogTitle>HTML 源代码</DialogTitle>
        </DialogHeader>
        <div class="flex-1 min-h-0 py-4">
          <textarea
            id="editor-source-html"
            name="editor-source-html"
            class={`${textareaClass} h-full font-mono text-sm leading-relaxed`}
            value={sourceHtml()}
            onInput={(e) => setSourceHtml(e.currentTarget.value)}
            spellcheck={false}
          />
        </div>
        <DialogFooter>
          <Button variant="secondary" onClick={props.onClose}>
            取消
          </Button>
          <Button onClick={applySource}>应用</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default SourceDialog;
