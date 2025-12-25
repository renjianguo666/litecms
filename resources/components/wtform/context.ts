import { createFormHookContexts } from '@tanstack/solid-form';

// 创建表单上下文
export const { fieldContext, formContext, useFieldContext, useFormContext } =
  createFormHookContexts();
