import { createSignal, onMount, onCleanup } from "solid-js";
import type { Editor } from "@tiptap/core";

/**
 * 编辑器状态更新 Hook
 *
 * 监听编辑器的 transaction 和 selectionUpdate 事件，
 * 返回一个版本号 accessor，在需要响应式更新的地方调用它。
 *
 * @param editor - Tiptap Editor 实例
 * @returns 版本号 accessor，每次编辑器更新时自增
 *
 * @example
 * ```tsx
 * function MyToolbar(props: { editor: Editor }) {
 *   const version = useEditorUpdate(props.editor);
 *
 *   const isBold = () => {
 *     version(); // 触发响应式更新
 *     return props.editor.isActive("bold");
 *   };
 *
 *   return <button class={isBold() ? "active" : ""}>Bold</button>;
 * }
 * ```
 */
export function useEditorUpdate(editor: Editor): () => number {
  const [version, setVersion] = createSignal(0);

  onMount(() => {
    const handler = () => setVersion((n) => n + 1);
    editor.on("transaction", handler);
    editor.on("selectionUpdate", handler);

    onCleanup(() => {
      editor.off("transaction", handler);
      editor.off("selectionUpdate", handler);
    });
  });

  return version;
}

export default useEditorUpdate;
