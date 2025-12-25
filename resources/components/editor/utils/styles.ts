/**
 * 共享样式常量
 * 用于编辑器各组件的统一样式
 */

/** 输入框基础样式 */
export const inputClass =
  "w-full h-10 px-3 text-sm bg-background border border-input rounded-md transition-colors placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring disabled:opacity-50 disabled:cursor-not-allowed";

/** 文本域基础样式 */
export const textareaClass =
  "w-full px-3 py-2 text-sm bg-background border border-input rounded-md transition-colors placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring resize-none";

/** 工具栏按钮基础样式 */
export const toolbarButtonClass =
  "inline-flex items-center justify-center size-8 rounded-md text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50";

/** 工具栏按钮激活状态样式 */
export const toolbarButtonActiveClass = "bg-accent text-accent-foreground";

/** 对话框内标签样式 */
export const labelClass = "text-sm font-medium";

/** 对话框内提示文字样式 */
export const hintClass = "text-xs text-muted-foreground";

/** 分隔线样式 */
export const dividerClass = "h-6 w-px bg-border mx-1";
