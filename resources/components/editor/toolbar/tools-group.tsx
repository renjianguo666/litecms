import type { Editor } from "@tiptap/core";
import { FileCode, Maximize, Minimize } from "lucide-solid";
import { ToolbarButton, ToolbarGroup } from "./button";

/**
 * 工具组属性
 */
export interface ToolsGroupProps {
  editor: Editor;
  /** 点击源代码按钮 */
  onSourceClick: () => void;
  /** 点击一键排版按钮 */
  onFormatClick: () => void;
  /** 点击全屏按钮 */
  onFullscreenClick: () => void;
  /** 是否全屏状态 */
  isFullscreen?: boolean;
}

/**
 * 工具组（一键排版、源代码、全屏）
 *
 * 提供编辑器辅助工具按钮。
 */
export function ToolsGroup(props: ToolsGroupProps) {
  return (
    <ToolbarGroup>
      <ToolbarButton onClick={props.onSourceClick} title="源代码">
        <FileCode class="w-4 h-4" />
      </ToolbarButton>
      <ToolbarButton
        onClick={props.onFullscreenClick}
        isActive={props.isFullscreen}
        title={props.isFullscreen ? "退出全屏" : "全屏"}
      >
        {props.isFullscreen ? (
          <Minimize class="w-4 h-4" />
        ) : (
          <Maximize class="w-4 h-4" />
        )}
      </ToolbarButton>
      <ToolbarButton
        onClick={props.onFormatClick}
        title="一键排版"
        class="w-auto px-2 text-xs whitespace-nowrap"
      >
        <span>一键排版</span>
      </ToolbarButton>
    </ToolbarGroup>
  );
}

export default ToolsGroup;
