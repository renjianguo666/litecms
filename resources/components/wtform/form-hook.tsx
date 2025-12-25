import type { JSX, Accessor, Component, ParentProps } from "solid-js";
import { splitProps } from "solid-js";
import { createFormHook } from "@tanstack/solid-form";
import type { FormOptions } from "@tanstack/solid-form";
import { fieldContext, formContext } from "./context";
import {
  StringField,
  NumberField,
  TextareaField,
  SelectField,
  CheckboxField,
  SwitchField,
  EditorField,
  ComboboxField,
  DatalistField,
} from "./fields";
import { SubmitButton, ResetButton } from "./buttons";
import type {
  StringFieldProps,
  NumberFieldProps,
  TextareaFieldProps,
  SelectFieldProps,
  CheckboxFieldProps,
  SwitchFieldProps,
  EditorFieldProps,
  ComboboxFieldProps,
  DatalistFieldProps,
  SubmitButtonProps,
  ResetButtonProps,
} from "./types";
import { toast } from "@/components/ui/toast";

// 字段组件映射
const fieldComponents = {
  StringField,
  NumberField,
  TextareaField,
  SelectField,
  CheckboxField,
  SwitchField,
  EditorField,
  ComboboxField,
  DatalistField,
};

// 表单组件映射
const formComponents = {
  SubmitButton,
  ResetButton,
};

// 创建基础表单 Hook
const { useAppForm: useBaseForm, withForm } = createFormHook({
  fieldContext,
  formContext,
  fieldComponents,
  formComponents,
});

// 带 name 的字段属性类型
type WithName<T> = T & { name: string };

// 基础表单返回类型
type BaseFormReturn = ReturnType<typeof useBaseForm>;

// 便捷字段方法的类型
interface BoundFields {
  StringField: (props: WithName<StringFieldProps>) => JSX.Element;
  NumberField: (props: WithName<NumberFieldProps>) => JSX.Element;
  TextareaField: (props: WithName<TextareaFieldProps>) => JSX.Element;
  SelectField: (props: WithName<SelectFieldProps>) => JSX.Element;
  CheckboxField: (props: WithName<CheckboxFieldProps>) => JSX.Element;
  SwitchField: (props: WithName<SwitchFieldProps>) => JSX.Element;
  EditorField: (props: WithName<EditorFieldProps>) => JSX.Element;
  ComboboxField: (props: WithName<ComboboxFieldProps>) => JSX.Element;
  DatalistField: (props: WithName<DatalistFieldProps>) => JSX.Element;
  SubmitButton: (props?: SubmitButtonProps) => JSX.Element;
  ResetButton: (props?: ResetButtonProps) => JSX.Element;
  Form: (props: ParentProps<{ class?: string }>) => JSX.Element;
}

// 字段组件的类型
type FieldComponents = typeof fieldComponents;
type FieldComponentKey = keyof FieldComponents;

/**
 * 创建绑定字段的高阶函数
 */
function createBoundField<K extends FieldComponentKey>(
  form: BaseFormReturn,
  componentKey: K,
) {
  type Props = Parameters<FieldComponents[K]>[0];

  return function BoundField(fieldProps: WithName<Props>): JSX.Element {
    // 使用 splitProps 保持响应式，不能用解构
    const [nameProps, restProps] = splitProps(fieldProps, ["name"]);
    return (
      <form.AppField name={nameProps.name as any}>
        {(field: any) => {
          const FieldComp = field[componentKey] as Component<Props>;
          return <FieldComp {...(restProps as Props)} />;
        }}
      </form.AppField>
    );
  };
}

/**
 * 增强版表单 Hook - 提供便捷的字段方法
 *
 * @example
 * ```tsx
 * const form = useWTForm(() => ({
 *   defaultValues: { name: '', email: '' },
 *   onSubmit: async ({ value }) => console.log(value),
 * }));
 *
 * return (
 *   <form.Form>
 *     <form.StringField name="name" label="姓名" />
 *     <form.StringField name="email" label="邮箱" type="email" />
 *     <form.SubmitButton>提交</form.SubmitButton>
 *   </form.Form>
 * );
 * ```
 */
export function useWTForm<TData extends Record<string, any>>(
  options: Accessor<
    FormOptions<TData, any, any, any, any, any, any, any, any, any, any, any>
  >,
): BaseFormReturn & BoundFields {
  const form = useBaseForm(options as any);

  // 创建便捷字段方法
  const boundFields: BoundFields = {
    StringField: createBoundField(form, "StringField"),
    NumberField: createBoundField(form, "NumberField"),
    TextareaField: createBoundField(form, "TextareaField"),
    SelectField: createBoundField(form, "SelectField"),
    CheckboxField: createBoundField(form, "CheckboxField"),
    SwitchField: createBoundField(form, "SwitchField"),
    EditorField: createBoundField(form, "EditorField"),
    ComboboxField: createBoundField(form, "ComboboxField"),
    DatalistField: createBoundField(form, "DatalistField"),
    // 按钮组件（包含 AppForm context）
    SubmitButton: (props: SubmitButtonProps = {}) => (
      <form.AppForm>
        <SubmitButton {...props} />
      </form.AppForm>
    ),
    ResetButton: (props: ResetButtonProps = {}) => (
      <form.AppForm>
        <ResetButton {...props} />
      </form.AppForm>
    ),
    // Form 容器组件
    Form: (props: ParentProps<{ class?: string }>) => (
      <form.AppForm>
        <form
          class={props.class}
          onSubmit={async (e) => {
            e.preventDefault();
            e.stopPropagation();
            try {
              await form.handleSubmit();
            } catch (error: any) {
              // 有字段错误 → 设置到对应字段
              if (error.extra?.length) {
                error.extra.forEach(({ field, message }: { field: string; message: string }) => {
                  form.setFieldMeta(field, (prev: any) => ({
                    ...prev,
                    errorMap: { onChange: message },
                  }));
                });
              } else {
                // 无字段错误 → 显示 toast
                toast.error(error.detail || "操作失败");
              }
            }
          }}
        >
          {props.children}
        </form>
      </form.AppForm>
    ),
  };

  return Object.assign(form, boundFields);
}

// 导出原始 hook 以便需要时使用
export { useBaseForm as useAppForm, withForm };
