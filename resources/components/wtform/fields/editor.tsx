import { Show, onCleanup } from "solid-js";
import { useFieldContext } from "../context";
import { RichEditor, type EditorRef } from "@/components/editor";
import type { EditorFieldProps } from "../types";

export function EditorField(props: EditorFieldProps) {
  const field = useFieldContext<string>();

  // 编辑器引用
  let editorRef: EditorRef | null = null;

  // 获取 field 实例（只调用一次）
  const fieldApi = field();

  // 用于区分用户输入和外部变更
  let isUserInput = false;
  let lastKnownValue = fieldApi.state.value ?? "";

  const hasError = () => {
    return (
      fieldApi.state.meta.isTouched && fieldApi.state.meta.errors.length > 0
    );
  };

  const errorMessages = () => {
    return fieldApi.state.meta.errors
      .map((e: any) => (typeof e === "string" ? e : (e?.message ?? "")))
      .join(", ");
  };

  // onChange 处理函数
  const handleChange = (html: string) => {
    isUserInput = true;
    lastKnownValue = html;
    fieldApi.handleChange(html);
    // 重置标记（延迟，确保 store 更新完成）
    queueMicrotask(() => {
      isUserInput = false;
    });
  };

  // 编辑器就绪回调
  const handleReady = (ref: EditorRef) => {
    editorRef = ref;

    // 订阅 form store，监听值变化
    const unsubscribe = fieldApi.form.store.subscribe(() => {
      // 获取当前字段值
      const currentValue = fieldApi.state.value ?? "";

      // 如果是用户输入导致的变化，跳过
      if (isUserInput) {
        return;
      }

      // 如果值变了（外部变更，如重置），同步到编辑器
      if (currentValue !== lastKnownValue && editorRef) {
        lastKnownValue = currentValue;
        editorRef.setContent(currentValue);
      }
    });

    // 组件卸载时取消订阅
    onCleanup(() => {
      unsubscribe();
    });
  };

  // 获取初始值
  const initialContent = fieldApi.state.value ?? "";

  return (
    <div class="w-full space-y-1.5">
      <Show when={props.label}>
        <span class="text-sm font-medium">{props.label}</span>
      </Show>
      <RichEditor
        content={initialContent}
        onChange={handleChange}
        onReady={handleReady}
        placeholder={props.placeholder}
        minHeight={props.minHeight}
        maxHeight={props.maxHeight}
        showWordCount={props.showWordCount}
        readonly={props.disabled}
        class={hasError() ? "border-destructive" : ""}
        onImageUpload={props.onImageUpload}
      />
      <Show when={props.description && !hasError()}>
        <p class="text-xs text-muted-foreground">{props.description}</p>
      </Show>
      <Show when={hasError()}>
        <p class="text-xs text-destructive">{errorMessages()}</p>
      </Show>
    </div>
  );
}
