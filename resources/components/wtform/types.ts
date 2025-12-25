import type { JSX } from "solid-js";

/**
 * 选项类型
 */
export interface SelectOption {
  label: string;
  value: string;
}

/**
 * 多选选项类型
 */
export interface ComboboxOption {
  label: string;
  value: string;
}

/**
 * 基础字段属性
 */
export interface BaseFieldProps {
  label?: string;
  description?: string;
  disabled?: boolean;
}

/**
 * 字符串字段属性
 */
export interface StringFieldProps extends BaseFieldProps {
  placeholder?: string;
  type?: "text" | "email" | "password" | "url" | "tel";
}

/**
 * 数字字段属性
 */
export interface NumberFieldProps extends BaseFieldProps {
  placeholder?: string;
  min?: number;
  max?: number;
  step?: number;
}

/**
 * 文本域字段属性
 */
export interface TextareaFieldProps extends BaseFieldProps {
  placeholder?: string;
  rows?: number;
}

/**
 * 选择字段属性
 */
export interface SelectFieldProps extends BaseFieldProps {
  placeholder?: string;
  options: SelectOption[];
  /** 是否允许空值，为 true 时空字符串会转为 null */
  nullable?: boolean;
}

/**
 * 复选框字段属性
 */
export interface CheckboxFieldProps {
  label: string;
  description?: string;
  disabled?: boolean;
}

/**
 * 开关字段属性
 */
export interface SwitchFieldProps {
  label: string;
  description?: string;
  disabled?: boolean;
}

/**
 * 多选字段属性
 */
export interface ComboboxFieldProps extends BaseFieldProps {
  /** 选项列表 */
  options: ComboboxOption[];
  /** 占位符 */
  placeholder?: string;
  /** 搜索框占位符 */
  searchPlaceholder?: string;
}

/**
 * 单选建议字段属性（类似 HTML datalist）
 */
export interface DatalistFieldProps extends BaseFieldProps {
  /** 建议选项列表 */
  options: ComboboxOption[];
  /** 占位符 */
  placeholder?: string;
}

/**
 * 富文本编辑器字段属性
 */
export interface EditorFieldProps extends BaseFieldProps {
  placeholder?: string;
  /** 编辑器最小高度 */
  minHeight?: string;
  /** 编辑器最大高度 */
  maxHeight?: string;
  /** 是否显示字数统计 */
  showWordCount?: boolean;
  /** 图片上传回调，返回图片 URL */
  onImageUpload?: (file: File) => Promise<string>;
}

/**
 * 提交按钮属性
 */
export interface SubmitButtonProps {
  children?: JSX.Element | string;
  class?: string;
}

/**
 * 重置按钮属性
 */
export interface ResetButtonProps {
  children?: JSX.Element | string;
  class?: string;
  variant?: "outline" | "ghost";
}
