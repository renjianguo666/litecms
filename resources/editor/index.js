/**
 * LitecmsEditor 入口模块
 * 基于 Tiptap v3 的富文本编辑器,纯原生 JS。
 *
 * 初始化方式:
 *   模板里用内联 <script> 调用 createEditor,配置走 JS 对象(主流富文本编辑器模式)
 *   htmx 默认会执行 swap 进来的 <script>(allowScriptTags: true)
 *
 * 自动销毁:
 *   MutationObserver 监听 root.parentNode,当 root 被 HTMX swap 移除时自动调 destroy(),
 *   清理 document 级监听(search panel 的 mousemove/mouseup),避免内存泄漏
 */

import { setupCsrf } from "./utils/csrf.js";
import { Editor } from "@tiptap/core";
import { buildExtensions } from "./core/extensions.js";
import {
  buildToolbar,
  updateToolbarState,
  updateHistoryState,
} from "./toolbar.js";
import { createSharedModal } from "./dialogs/modal.js";
import { getLinkDialogConfig } from "./dialogs/link.js";
import { getImageDialogConfig } from "./dialogs/image.js";
import { getVideoDialogConfig } from "./dialogs/video.js";
import { getSourceDialogConfig } from "./dialogs/source.js";
import { createSearchPanel } from "./panels/search.js";
import { formatHtmlContent, cleanEditorHtml } from "./utils/format.js";
import { el } from "./utils/dom.js";

// 全局副作用:劫持 window.fetch,给非安全方法(POST/PUT/PATCH/DELETE)自动注入 X-CSRFToken
// 模块加载时执行一次,多次 import 也安全(内部有幂等检查)
setupCsrf();

const DEFAULT_PLACEHOLDER = "请输入内容...";
const DEFAULT_HEIGHT = "300px";
const DEFAULT_MIN_HEIGHT = "100px";
const DEFAULT_MAX_HEIGHT = "800px";

export function createEditor(target, options = {}) {
  let root =
    typeof target === "string" ? document.querySelector(target) : target;
  if (!root) throw new Error("[LitecmsEditor] 无法解析目标元素: " + target);

  // 便捷:直接传 textarea 时,自动创建挂载容器、隐藏原元素、接管为同步目标
  // 并用 textarea 的值作为初始内容,调用方无需手动建 div 和传 content
  if (root instanceof HTMLTextAreaElement) {
    const wrapper = document.createElement("div");
    root.parentNode.insertBefore(wrapper, root.nextSibling);
    root.hidden = true;
    if (!options.syncTarget) options.syncTarget = root;
    if (options.content === undefined) options.content = root.value;
    root = wrapper;
  }

  const placeholder = options.placeholder || DEFAULT_PLACEHOLDER;
  const height = options.height || DEFAULT_HEIGHT;
  const minHeight = options.minHeight || DEFAULT_MIN_HEIGHT;
  const maxHeight = options.maxHeight || DEFAULT_MAX_HEIGHT;
  const uploadUrl = options.uploadUrl;
  const skipOrigins = options.skipOrigins || [];
  const inputName = options.inputName || "";
  const initialContent = options.content || "";
  const characterLimit = options.characterLimit || 0;
  const syncTarget = options.syncTarget || null;

  let editor = null;
  let sharedModal = null;
  let dialogConfigs = null;
  let searchPanel = null;
  let syncTimer = null;
  let toolbarUpdateScheduled = false;
  let destroyed = false;

  // ===== 1. 创建全部 DOM,直接挂到 root(不再套一层 container) =====
  root.className =
    "litecms-editor border rounded-box overflow-hidden relative bg-base-100";

  const contentWrap = el(
    "div",
    "editor-content bg-base-100 cursor-text relative",
  );
  // 尺寸用 inline style 写在父元素上,不碰 .ProseMirror,不会 reflow
  contentWrap.style.height = height;
  contentWrap.style.minHeight = minHeight;
  contentWrap.style.maxHeight = maxHeight;

  const mountEl = el("div", "editor-mount h-full");
  contentWrap.appendChild(mountEl);
  root.appendChild(contentWrap);

  const statusBar = el(
    "div",
    "editor-status-bar shrink-0 flex items-center justify-end gap-3 px-3 py-1 text-xs text-base-content/60 bg-base-200 border-t border-base-300",
  );
  const charCountSpan = el("span", null, "0 字符");
  statusBar.appendChild(charCountSpan);
  root.appendChild(statusBar);

  function toggleFullscreen() {
    const isFs = root.classList.toggle("is-fullscreen");
    document.body.style.overflow = isFs ? "hidden" : "";
  }

  const toolbarEl = buildToolbar(() => editor, {
    onDialog: (name) => sharedModal?.open(dialogConfigs?.[name]),
    onSearch: () => searchPanel?.open(),
    onFullscreen: toggleFullscreen,
    onFormat: () => {
      if (!editor) return;
      const formatted = formatHtmlContent(editor.getHTML());
      editor.chain().focus().setContent(formatted).run();
    },
  });
  root.insertBefore(toolbarEl, contentWrap);

  let syncEl = syncTarget;
  if (!syncEl && inputName) {
    syncEl = el("input");
    syncEl.type = "hidden";
    syncEl.name = inputName;
    syncEl.value = initialContent;
    root.appendChild(syncEl);
  }

  // ===== 辅助函数 =====
  function syncToInputImmediate() {
    if (!syncEl || !editor) return;
    clearTimeout(syncTimer);
    syncEl.value = cleanEditorHtml(editor.getHTML());
  }
  function syncToInput() {
    if (!syncEl || !editor) return;
    clearTimeout(syncTimer);
    syncTimer = setTimeout(syncToInputImmediate, 500);
  }

  function updateCharCount() {
    if (!editor) return;
    const count = editor.storage.characterCount.characters();
    if (characterLimit > 0) {
      charCountSpan.textContent = `${count} / ${characterLimit} 字符`;
      charCountSpan.classList.toggle("text-error", count > characterLimit);
    } else {
      charCountSpan.textContent = `${count} 字符`;
      charCountSpan.classList.remove("text-error");
    }
  }

  // 工具栏状态更新:延迟到 microtask,避免在 ProseMirror 事务中同步调 isActive()
  function scheduleToolbarUpdate() {
    if (toolbarUpdateScheduled || !toolbarEl) return;
    toolbarUpdateScheduled = true;
    queueMicrotask(() => {
      toolbarUpdateScheduled = false;
      if (!editor) return;
      updateToolbarState(editor, toolbarEl);
      updateHistoryState(editor, toolbarEl);
    });
  }

  const onContentChange = () => {
    syncToInput();
    updateCharCount();
    scheduleToolbarUpdate();
  };

  // ===== 2. 创建 Tiptap Editor =====
  function initEditor() {
    if (destroyed) return;
    editor = new Editor({
      element: mountEl,
      extensions: buildExtensions({
        placeholder,
        characterLimit,
        uploadUrl,
        skipOrigins,
      }),
      content: initialContent,
      editorProps: {
        attributes: {
          class: "prose max-w-none p-4 focus:outline-none",
        },
      },
      onUpdate: onContentChange,
    });


    editor.on("selectionUpdate", scheduleToolbarUpdate);
    editor.on("transaction", scheduleToolbarUpdate);

    updateCharCount();

    // 延迟到 microtask:sharedModal / searchPanel 的 DOM 创建不跟 new Editor() 挤同一帧
    queueMicrotask(() => {
      if (destroyed || !editor) return;
      sharedModal = createSharedModal();
      root.appendChild(sharedModal.el);

      dialogConfigs = {
        link: getLinkDialogConfig(editor),
        image: getImageDialogConfig(editor, uploadUrl),
        video: getVideoDialogConfig(editor),
        source: getSourceDialogConfig(editor),
      };

      searchPanel = createSearchPanel(editor);
      contentWrap.appendChild(searchPanel.el);
      scheduleToolbarUpdate();
    });
  }

  initEditor();

  // ===== 表单 & 快捷键 =====
  const form = root.closest("form");
  function onFormSubmit() {
    syncToInputImmediate();
  }
  if (form) form.addEventListener("submit", onFormSubmit, { capture: true });

  function handleKeydown(event) {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "f") {
      event.preventDefault();
      searchPanel?.open();
      return;
    }
    if (event.key === "Escape") {
      // 查找替换面板:非原生 dialog,需要手动关
      if (searchPanel && searchPanel.el.style.display !== "none") {
        event.preventDefault();
        searchPanel.close();
        return;
      }
      // 原生 <dialog> 打开时,ESC 的原生行为就是关闭 dialog
      // 不能 preventDefault(),否则会阻止 dialog 关闭
      // 只有当没有任何 dialog 打开时,ESC 才退出全屏
      if (!sharedModal?.el?.open && root.classList.contains("is-fullscreen")) {
        event.preventDefault();
        toggleFullscreen();
      }
    }
  }

  root.addEventListener("keydown", handleKeydown);

  // ===== 自动销毁:监听 root 从 DOM 移除(HTMX swap 等) =====
  // search panel 在 document 上注册了 mousemove/mouseup 监听,
  // 如果不调 destroy(),这些监听永远不会被清理,每次 HTMX 导航都泄漏一份
  const cleanupObserver = new MutationObserver(() => {
    if (!destroyed && !root.isConnected) {
      destroy();
    }
  });
  if (root.parentNode) {
    cleanupObserver.observe(root.parentNode, { childList: true });
  }

  function destroy() {
    if (destroyed) return;
    destroyed = true;

    // 先断开 observer,避免 destroy 内部的 DOM 操作再次触发回调
    cleanupObserver.disconnect();

    root.removeEventListener("keydown", handleKeydown);
    if (form) form.removeEventListener("submit", onFormSubmit);

    // 关闭可能打开的 <dialog>,避免 top layer 残留
    if (sharedModal?.el?.open) sharedModal.el.close();

    // searchPanel.destroy() 要在 editor.destroy() 之前,
    // 因为它需要调 editor.off("update", ...) 移除监听
    if (searchPanel) searchPanel.destroy();

    if (editor) {
      editor.off("selectionUpdate", scheduleToolbarUpdate);
      editor.off("transaction", scheduleToolbarUpdate);
      editor.destroy();
    }

    root.remove();
    if (syncEl && !syncTarget) syncEl.remove();
  }

  return {
    get editor() {
      return editor;
    },
    getHTML: () => (editor ? cleanEditorHtml(editor.getHTML()) : ""),
    setHTML: (html) => editor?.commands.setContent(html),
    getText: () => (editor ? editor.getText() : ""),
    focus: () => editor?.commands.focus(),
    clear: () => editor?.commands.clearContent(),
    destroy,
  };
}
