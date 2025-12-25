import {
  createSignal,
  onMount,
  onCleanup,
  Show,
  createEffect,
  splitProps,
} from "solid-js";
import { Editor } from "@tiptap/core";
import type { EditorProps, EditorRef } from "./types";
import { getDefaultExtensions } from "./core/index";
import { MenuBar } from "./toolbar/index";
import { SearchPanel, StatusBar } from "./panels/index";
import { EditorErrorBoundary } from "./error";
import { cleanEditorHtml } from "./utils/format";
import { EDITOR_CONFIG } from "./constants";
import "./styles.css";

// 类型导出
export type { EditorProps, EditorRef } from "./types";
export type { DialogType, VideoType } from "./types";

// 核心模块导出
export { getDefaultExtensions, Video, Iframe } from "./core/index";

// 工具栏组件导出
export {
  ToolbarButton,
  ToolbarDivider,
  ToolbarGroup,
  HistoryGroup,
  FormatGroup,
  ColorGroup,
  AlignGroup,
  MediaGroup,
  ToolsGroup,
  SearchGroup,
  MenuBar,
} from "./toolbar/index";

// 对话框组件导出
export {
  LinkDialog,
  ImageDialog,
  VideoDialog,
  SourceDialog,
} from "./dialogs/index";

// 面板组件导出
export { SearchPanel, StatusBar } from "./panels/index";

// Hooks 导出
export { useEditorUpdate } from "./hooks/index";

// 工具函数导出
export {
  formatHtmlContent,
  cleanEditorHtml,
  cleanAttributes,
  addParagraphIndent,
} from "./utils/format";

export {
  validateAndSanitizeUrl,
  convertToEmbedUrl,
  isValidEmbedUrl,
  isValidHttpUrl,
  sanitizeMediaUrl,
} from "./utils/security";

/**
 * 富文本编辑器组件（带错误边界）
 */
export function RichEditor(props: EditorProps) {
  return (
    <EditorErrorBoundary>
      <RichEditorCore {...props} />
    </EditorErrorBoundary>
  );
}

/**
 * 编辑器核心组件
 *
 * 采用非受控模式：初始内容通过 props.content 传入，后续变化通过 onChange 回调输出。
 * 不监听 props.content 的变化，以保留编辑器的撤销/重做历史。
 *
 * 全屏模式使用纯 CSS 实现（fixed 定位），不使用 Portal，
 * 这样可以保持正常的 DOM 层级，避免与工具栏中的 Dialog 组件产生 z-index 冲突。
 */
function RichEditorCore(props: EditorProps) {
  // 分离组件特定属性和需要透传的 HTML 属性
  const [local, rest] = splitProps(props, [
    "content",
    "placeholder",
    "readonly",
    "onChange",
    "class",
    "minHeight",
    "maxHeight",
    "showWordCount",
    "onImageUpload",
    "onReady",
  ]);

  const [editor, setEditor] = createSignal<Editor | null>(null);
  const [isFullscreen, setIsFullscreen] = createSignal(false);
  const [showSearch, setShowSearch] = createSignal(false);
  const [wordCount, setWordCount] = createSignal({ characters: 0, words: 0 });
  let editorContainer: HTMLDivElement | undefined;
  let contentWrapper: HTMLDivElement | undefined;

  // 统计字数
  const updateWordCount = (ed: Editor) => {
    const text = ed.getText();
    // 中文字符数
    const chineseChars = (text.match(/[\u4e00-\u9fa5]/g) || []).length;
    // 英文单词数
    const englishWords = text
      .replace(/[\u4e00-\u9fa5]/g, " ")
      .split(/\s+/)
      .filter((word) => word.length > 0).length;

    setWordCount({
      characters: text.length,
      words: chineseChars + englishWords,
    });
  };

  onMount(() => {
    if (!editorContainer) return;

    const instance = new Editor({
      element: editorContainer,
      extensions: getDefaultExtensions({
        placeholder: local.placeholder || EDITOR_CONFIG.defaultPlaceholder,
      }),
      content: local.content || "",
      editable: !local.readonly,
      editorProps: {
        attributes: {
          class:
            "prose prose-sm [&_p]:my-3 [&_p]:leading-relaxed max-w-none h-full min-h-full p-4 focus:outline-none cursor-text",
        },
        transformPastedHTML(html) {
          if (!html) return html;

          const parser = new DOMParser();
          const doc = parser.parseFromString(html, "text/html");

          // 3. 批量移除
          doc.querySelectorAll("[style], [class]").forEach((node) => {
            node.removeAttribute("style");
            node.removeAttribute("class");
          });

          return doc.body.innerHTML;
        },
      },
      onUpdate: ({ editor: ed }) => {
        const html = cleanEditorHtml(ed.getHTML());
        local.onChange?.(html);

        // 更新字数统计
        if (local.showWordCount) {
          updateWordCount(ed);
        }
      },
    });

    setEditor(instance);

    // 初始化字数统计
    if (local.showWordCount) {
      updateWordCount(instance);
    }

    // 调用 onReady 回调，暴露编辑器引用
    if (local.onReady) {
      const editorRef: EditorRef = {
        getEditor: () => instance,
        setContent: (html: string) => {
          instance.commands.setContent(html, { emitUpdate: false });
          if (local.showWordCount) {
            updateWordCount(instance);
          }
        },
        getHTML: () => cleanEditorHtml(instance.getHTML()),
        getText: () => instance.getText(),
        focus: () => instance.commands.focus(),
        clear: () => {
          instance.commands.clearContent();
          if (local.showWordCount) {
            updateWordCount(instance);
          }
        },
      };
      local.onReady(editorRef);
    }

    // 键盘快捷键：Ctrl+F 打开查找面板
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "f") {
        e.preventDefault();
        setShowSearch(true);
      }
      // Escape 关闭查找面板或退出全屏
      if (e.key === "Escape") {
        if (showSearch()) {
          setShowSearch(false);
        } else if (isFullscreen()) {
          setIsFullscreen(false);
        }
      }
    };

    editorContainer.addEventListener("keydown", handleKeyDown);

    onCleanup(() => {
      editorContainer?.removeEventListener("keydown", handleKeyDown);
    });
  });

  onCleanup(() => {
    editor()?.destroy();
  });

  // 监听只读状态
  createEffect(() => {
    const ed = editor();
    if (ed) {
      ed.setEditable(!local.readonly);
    }
  });

  // 全屏时禁止 body 滚动
  createEffect(() => {
    if (isFullscreen()) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
  });

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen());
  };

  const toggleSearch = () => {
    setShowSearch(!showSearch());
  };

  const baseClass =
    "border border-border rounded-lg overflow-hidden bg-card flex flex-col focus-within:border-ring focus-within:ring-ring/50 focus-within:ring-[3px]";

  const containerClass = () => {
    if (isFullscreen()) {
      // 全屏模式：使用 fixed 定位覆盖整个视口
      return `${baseClass} fixed inset-0 z-[1000] rounded-none`;
    }
    return `${baseClass} relative ${local.class || ""}`;
  };

  return (
    <div class={containerClass()} {...rest}>
      {/* 菜单栏 */}
      <Show when={!local.readonly}>
        <MenuBar
          editor={editor}
          onFullscreen={toggleFullscreen}
          isFullscreen={isFullscreen()}
          onSearchClick={toggleSearch}
          onImageUpload={local.onImageUpload}
        />
      </Show>

      {/* 编辑器内容区 - 相对定位容器 */}
      <div
        ref={contentWrapper}
        class={`relative ${isFullscreen() ? "flex-1 min-h-0" : ""}`}
        style={{
          height: isFullscreen()
            ? undefined
            : local.minHeight || EDITOR_CONFIG.defaultMinHeight,
          "min-height": isFullscreen() ? undefined : "100px",
          "max-height": isFullscreen() ? undefined : local.maxHeight || "800px",
          resize: isFullscreen() || local.readonly ? "none" : "vertical",
          overflow: "hidden",
        }}
      >
        {/* 查找替换面板 - 固定在内容区右上角 */}
        <Show when={showSearch()}>
          <SearchPanel editor={editor} onClose={() => setShowSearch(false)} />
        </Show>

        {/* 编辑器内容 - 内部滚动 */}
        <div ref={editorContainer} class="overflow-auto h-full" />
      </div>

      {/* 状态栏（字数统计） */}
      <Show when={local.showWordCount && !local.readonly}>
        <StatusBar
          characters={wordCount().characters}
          words={wordCount().words}
        />
      </Show>
    </div>
  );
}

// 默认导出
export default RichEditor;
