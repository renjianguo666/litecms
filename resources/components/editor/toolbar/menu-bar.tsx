import { createSignal, Show, type Accessor } from "solid-js";
import type { Editor } from "@tiptap/core";
import type { DialogType } from "../types";
import { formatHtmlContent } from "../utils/format";

// 工具栏组件
import { HistoryGroup } from "./history-group";
import { SearchGroup } from "./search-group";
import { FormatGroup } from "./format-group";
import { ColorGroup } from "./color-group";
import { AlignGroup } from "./align-group";
import { MediaGroup } from "./media-group";
import { ToolsGroup } from "./tools-group";

// 对话框组件
import { LinkDialog } from "../dialogs/link-dialog";
import { ImageDialog } from "../dialogs/image-dialog";
import { VideoDialog } from "../dialogs/video-dialog";
import { SourceDialog } from "../dialogs/source-dialog";

/**
 * 菜单栏属性
 */
export interface MenuBarProps {
  /** 编辑器实例 */
  editor: Accessor<Editor | null>;
  /** 全屏切换回调 */
  onFullscreen?: () => void;
  /** 是否全屏状态 */
  isFullscreen?: boolean;
  /** 搜索面板切换回调 */
  onSearchClick?: () => void;
  /** 图片上传回调 */
  onImageUpload?: (file: File) => Promise<string>;
}

/**
 * 菜单栏组件
 *
 * 整合所有工具栏按钮组和对话框。
 */
export function MenuBar(props: MenuBarProps) {
  const [activeDialog, setActiveDialog] = createSignal<DialogType>(null);

  const editor = () => props.editor();

  // 打开对话框
  const openDialog = (type: DialogType) => {
    if (type === "search") {
      // 搜索通过回调触发，由父组件处理
      props.onSearchClick?.();
    } else {
      setActiveDialog(type);
    }
  };

  // 关闭对话框
  const closeDialog = () => {
    setActiveDialog(null);
  };

  // 一键排版
  const handleFormat = () => {
    const ed = editor();
    if (!ed) return;

    const html = ed.getHTML();
    const formatted = formatHtmlContent(html);
    ed.chain().focus().setContent(formatted).run();
  };

  return (
    <div class="border-b border-border bg-card relative">
      {/* 工具栏 */}
      <Show when={editor()}>
        {(ed) => (
          <div class="flex flex-wrap items-center gap-0.5 p-1">
            {/* 撤销/重做 */}
            <HistoryGroup editor={ed()} />

            {/* 查找替换 */}
            <SearchGroup onSearchClick={() => openDialog("search")} />

            {/* 格式化 */}
            <FormatGroup editor={ed()} />

            {/* 颜色 */}
            <ColorGroup editor={ed()} />

            {/* 对齐 */}
            <AlignGroup editor={ed()} />

            {/* 媒体插入 */}
            <MediaGroup
              editor={ed()}
              onLinkClick={() => openDialog("link")}
              onImageClick={() => openDialog("image")}
              onVideoClick={() => openDialog("video")}
            />

            {/* 工具 */}
            <ToolsGroup
              editor={ed()}
              onFormatClick={handleFormat}
              onSourceClick={() => openDialog("source")}
              onFullscreenClick={() => props.onFullscreen?.()}
              isFullscreen={props.isFullscreen}
            />
          </div>
        )}
      </Show>

      {/* 链接对话框 */}
      <LinkDialog
        open={activeDialog() === "link"}
        onClose={closeDialog}
        editor={props.editor}
      />

      {/* 图片对话框 */}
      <ImageDialog
        open={activeDialog() === "image"}
        onClose={closeDialog}
        editor={props.editor}
        onImageUpload={props.onImageUpload}
      />

      {/* 视频对话框 */}
      <VideoDialog
        open={activeDialog() === "video"}
        onClose={closeDialog}
        editor={props.editor}
      />

      {/* 源代码对话框 */}
      <SourceDialog
        open={activeDialog() === "source"}
        onClose={closeDialog}
        editor={props.editor}
      />
    </div>
  );
}

export default MenuBar;
