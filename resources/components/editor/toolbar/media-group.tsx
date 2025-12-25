import type { Editor } from "@tiptap/core";
import { Link, Image, Video } from "lucide-solid";
import { useEditorUpdate } from "../hooks";
import { ToolbarButton, ToolbarGroup } from "./button";

/**
 * 媒体组属性
 */
export interface MediaGroupProps {
  editor: Editor;
  /** 点击链接按钮 */
  onLinkClick: () => void;
  /** 点击图片按钮 */
  onImageClick: () => void;
  /** 点击视频按钮 */
  onVideoClick: () => void;
}

/**
 * 媒体插入组（链接、图片、视频）
 *
 * 提供媒体插入功能按钮，点击后触发对应的回调打开对话框。
 */
export function MediaGroup(props: MediaGroupProps) {
  const version = useEditorUpdate(props.editor);

  const isActive = (name: string) => {
    version();
    return props.editor.isActive(name);
  };

  return (
    <ToolbarGroup>
      <ToolbarButton
        onClick={props.onLinkClick}
        isActive={isActive("link")}
        title="插入链接"
      >
        <Link class="w-4 h-4" />
      </ToolbarButton>
      <ToolbarButton onClick={props.onImageClick} title="插入图片">
        <Image class="w-4 h-4" />
      </ToolbarButton>
      <ToolbarButton onClick={props.onVideoClick} title="插入视频">
        <Video class="w-4 h-4" />
      </ToolbarButton>
    </ToolbarGroup>
  );
}

export default MediaGroup;
