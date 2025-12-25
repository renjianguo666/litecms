import type { Editor } from "@tiptap/core";
import { Bold, Italic, Underline, Strikethrough } from "lucide-solid";
import { useEditorUpdate } from "../hooks";
import { ToolbarButton, ToolbarGroup } from "./button";

/**
 * 格式化组属性
 */
export interface FormatGroupProps {
  editor: Editor;
}

/**
 * 格式化按钮组（加粗、斜体、下划线、删除线）
 *
 * 提供文本格式化功能按钮，自动响应编辑器状态变化。
 */
export function FormatGroup(props: FormatGroupProps) {
  const version = useEditorUpdate(props.editor);

  const isActive = (name: string) => {
    version();
    return props.editor.isActive(name);
  };

  return (
    <ToolbarGroup>
      <ToolbarButton
        onClick={() => props.editor.chain().focus().toggleBold().run()}
        isActive={isActive("bold")}
        title="加粗 (Ctrl+B)"
      >
        <Bold class="w-4 h-4" />
      </ToolbarButton>
      <ToolbarButton
        onClick={() => props.editor.chain().focus().toggleItalic().run()}
        isActive={isActive("italic")}
        title="斜体 (Ctrl+I)"
      >
        <Italic class="w-4 h-4" />
      </ToolbarButton>
      <ToolbarButton
        onClick={() => props.editor.chain().focus().toggleUnderline().run()}
        isActive={isActive("underline")}
        title="下划线 (Ctrl+U)"
      >
        <Underline class="w-4 h-4" />
      </ToolbarButton>
      <ToolbarButton
        onClick={() => props.editor.chain().focus().toggleStrike().run()}
        isActive={isActive("strike")}
        title="删除线"
      >
        <Strikethrough class="w-4 h-4" />
      </ToolbarButton>
    </ToolbarGroup>
  );
}

export default FormatGroup;
