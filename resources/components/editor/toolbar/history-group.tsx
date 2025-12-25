import type { Editor } from "@tiptap/core";
import { Undo2, Redo2 } from "lucide-solid";
import { useEditorUpdate } from "../hooks";
import { ToolbarButton, ToolbarGroup } from "./button";

/**
 * 历史操作组属性
 */
export interface HistoryGroupProps {
  editor: Editor;
}

/**
 * 历史操作组（撤销/重做）
 *
 * 提供撤销和重做功能按钮，自动响应编辑器状态变化。
 */
export function HistoryGroup(props: HistoryGroupProps) {
  const version = useEditorUpdate(props.editor);

  // 使用 version() 触发响应式更新
  const canUndo = () => {
    version();
    return props.editor.can().undo();
  };

  const canRedo = () => {
    version();
    return props.editor.can().redo();
  };

  return (
    <ToolbarGroup>
      <ToolbarButton
        onClick={() => props.editor.chain().focus().undo().run()}
        disabled={!canUndo()}
        title="撤销 (Ctrl+Z)"
      >
        <Undo2 class="w-4 h-4" />
      </ToolbarButton>
      <ToolbarButton
        onClick={() => props.editor.chain().focus().redo().run()}
        disabled={!canRedo()}
        title="重做 (Ctrl+Y)"
      >
        <Redo2 class="w-4 h-4" />
      </ToolbarButton>
    </ToolbarGroup>
  );
}

export default HistoryGroup;
