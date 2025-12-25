import { Show, type JSX } from "solid-js";
import {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

/**
 * 工具栏按钮属性
 */
export interface ToolbarButtonProps {
  /** 点击事件 */
  onClick?: () => void;
  /** 是否激活状态 */
  isActive?: boolean;
  /** 是否禁用 */
  disabled?: boolean;
  /** 提示文字（使用 Tooltip 显示） */
  title?: string;
  /** 自定义样式类 */
  class?: string;
  /** 子元素 */
  children: JSX.Element;
}

/**
 * 工具栏按钮组件
 *
 * 提供统一的按钮样式和交互行为。
 * 当传入 title 时，使用 Tooltip 显示提示信息。
 *
 * @example
 * ```tsx
 * <ToolbarButton
 *   onClick={() => editor.chain().focus().toggleBold().run()}
 *   isActive={editor.isActive("bold")}
 *   title="加粗 (Ctrl+B)"
 * >
 *   <Bold class="w-4 h-4" />
 * </ToolbarButton>
 * ```
 */
export function ToolbarButton(props: ToolbarButtonProps) {
  const button = (
    <button
      type="button"
      class={cn(
        "inline-flex items-center justify-center size-8 rounded-md text-sm font-medium transition-colors",
        "hover:bg-accent hover:text-accent-foreground",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        "disabled:pointer-events-none disabled:opacity-50",
        props.isActive && "bg-accent text-accent-foreground",
        props.class,
      )}
      onClick={props.onClick}
      disabled={props.disabled}
    >
      {props.children}
    </button>
  );

  return (
    <Show when={props.title} fallback={button}>
      <Tooltip>
        <TooltipTrigger as="div" class="inline-flex">
          {button}
        </TooltipTrigger>
        <TooltipContent>{props.title}</TooltipContent>
      </Tooltip>
    </Show>
  );
}

/**
 * 工具栏分隔符
 */
export function ToolbarDivider() {
  return <div class="h-6 w-px bg-border mx-1" />;
}

/**
 * 工具栏按钮组容器
 */
export interface ToolbarGroupProps {
  children: JSX.Element;
}

export function ToolbarGroup(props: ToolbarGroupProps) {
  return <div class="flex items-center">{props.children}</div>;
}

export default ToolbarButton;
