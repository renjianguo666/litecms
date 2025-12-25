import type { Editor } from "@tiptap/core";
import {
  TextAlignStart,
  TextAlignCenter,
  TextAlignEnd,
  TextAlignJustify,
} from "lucide-solid";
import { useEditorUpdate } from "../hooks";
import { ToolbarButton, ToolbarGroup } from "./button";

/**
 * 对齐组属性
 */
export interface AlignGroupProps {
  editor: Editor;
}

/**
 * 对齐按钮组（左对齐、居中、右对齐、两端对齐）
 *
 * 提供文本对齐功能按钮，自动响应编辑器状态变化。
 */
export function AlignGroup(props: AlignGroupProps) {
  const version = useEditorUpdate(props.editor);

  const isActive = (attrs: Record<string, unknown>) => {
    version();
    return props.editor.isActive(attrs);
  };

  return (
    <ToolbarGroup>
      <ToolbarButton
        onClick={() => props.editor.chain().focus().setTextAlign("left").run()}
        isActive={isActive({ textAlign: "left" })}
        title="左对齐"
      >
        <TextAlignStart class="w-4 h-4" />
      </ToolbarButton>
      <ToolbarButton
        onClick={() =>
          props.editor.chain().focus().setTextAlign("center").run()
        }
        isActive={isActive({ textAlign: "center" })}
        title="居中"
      >
        <TextAlignCenter class="w-4 h-4" />
      </ToolbarButton>
      <ToolbarButton
        onClick={() => props.editor.chain().focus().setTextAlign("right").run()}
        isActive={isActive({ textAlign: "right" })}
        title="右对齐"
      >
        <TextAlignEnd class="w-4 h-4" />
      </ToolbarButton>
      <ToolbarButton
        onClick={() =>
          props.editor.chain().focus().setTextAlign("justify").run()
        }
        isActive={isActive({ textAlign: "justify" })}
        title="两端对齐"
      >
        <TextAlignJustify class="w-4 h-4" />
      </ToolbarButton>
    </ToolbarGroup>
  );
}

export default AlignGroup;
