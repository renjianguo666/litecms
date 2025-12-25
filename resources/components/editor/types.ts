import type { Editor } from "@tiptap/core";
import type { JSX } from "solid-js";

/**
 * 编辑器实例引用
 * 用于外部命令式控制编辑器
 */
export interface EditorRef {
  /** 获取 Tiptap Editor 实例 */
  getEditor: () => Editor | null;
  /** 设置内容（不触发 onChange） */
  setContent: (html: string) => void;
  /** 获取 HTML 内容 */
  getHTML: () => string;
  /** 获取纯文本内容 */
  getText: () => string;
  /** 聚焦编辑器 */
  focus: () => void;
  /** 清空内容 */
  clear: () => void;
}

/**
 * 编辑器组件属性
 * 继承 HTMLAttributes 以支持透传所有 HTML 属性（如 aria-labelledby 等）
 */
export interface EditorProps extends Omit<
  JSX.HTMLAttributes<HTMLDivElement>,
  "onChange"
> {
  /** 初始 HTML 内容 */
  content?: string;
  /** 占位符文本 */
  placeholder?: string;
  /** 是否只读模式 */
  readonly?: boolean;
  /** 内容变化回调 */
  onChange?: (html: string) => void;
  /** 编辑器最小高度 */
  minHeight?: string;
  /** 编辑器最大高度（超出后滚动） */
  maxHeight?: string;
  /** 是否显示字数统计 */
  showWordCount?: boolean;
  /** 图片上传回调，返回图片 URL */
  onImageUpload?: (file: File) => Promise<string>;
  /** 编辑器就绪回调，返回编辑器引用 */
  onReady?: (ref: EditorRef) => void;
}

/**
 * 对话框类型
 */
export type DialogType =
  | "link"
  | "image"
  | "video"
  | "search"
  | "source"
  | null;

/**
 * 视频类型
 */
export type VideoType = "upload" | "embed";
