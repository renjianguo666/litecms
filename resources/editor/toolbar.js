import { parseTemplate } from "./utils/dom.js";

const COMMANDS = {
  undo: (e) => e.chain().focus().undo().run(),
  redo: (e) => e.chain().focus().redo().run(),
  bold: (e) => e.chain().focus().toggleBold().run(),
  italic: (e) => e.chain().focus().toggleItalic().run(),
  strike: (e) => e.chain().focus().toggleStrike().run(),
  underline: (e) => e.chain().focus().toggleUnderline().run(),
  alignLeft: (e) => e.chain().focus().setTextAlign("left").run(),
  alignCenter: (e) => e.chain().focus().setTextAlign("center").run(),
  alignRight: (e) => e.chain().focus().setTextAlign("right").run(),
  alignJustify: (e) => e.chain().focus().setTextAlign("justify").run(),
};

const ACTIVE_CHECKS = {
  bold: (e) => e.isActive("bold"),
  italic: (e) => e.isActive("italic"),
  strike: (e) => e.isActive("strike"),
  underline: (e) => e.isActive("underline"),
  alignLeft: (e) => e.isActive({ textAlign: "left" }),
  alignCenter: (e) => e.isActive({ textAlign: "center" }),
  alignRight: (e) => e.isActive({ textAlign: "right" }),
  alignJustify: (e) => e.isActive({ textAlign: "justify" }),
  link: (e) => e.isActive("link"),
};

const HANDLER_DISPATCH = {
  link: (h) => h.onDialog?.("link"),
  image: (h) => h.onDialog?.("image"),
  video: (h) => h.onDialog?.("video"),
  source: (h) => h.onDialog?.("source"),
  search: (h) => h.onSearch?.(),
  format: (h) => h.onFormat?.(),
  fullscreen: (h) => h.onFullscreen?.(),
};

const TOOLBAR_HTML = `
<div class="sticky top-0 z-10 shadow-sm flex flex-wrap items-center gap-1 p-1 bg-base-100 border-b border-base-300">
  <button type="button" data-cmd="undo" class="btn btn-sm btn-square btn-ghost tooltip tooltip-bottom" data-tip="撤销">
    <span class="icon-[lucide--undo] text-lg"></span>
  </button>
  <button type="button" data-cmd="redo" class="btn btn-sm btn-square btn-ghost tooltip tooltip-bottom" data-tip="重做">
    <span class="icon-[lucide--redo] text-lg"></span>
  </button>
  <div class="w-px h-6 bg-base-300 mx-1"></div>

  <button type="button" data-cmd="bold" class="btn btn-sm btn-square btn-ghost tooltip tooltip-bottom" data-tip="加粗">
    <span class="icon-[lucide--bold] text-lg"></span>
  </button>
  <button type="button" data-cmd="italic" class="btn btn-sm btn-square btn-ghost tooltip tooltip-bottom" data-tip="斜体">
    <span class="icon-[lucide--italic] text-lg"></span>
  </button>
  <button type="button" data-cmd="strike" class="btn btn-sm btn-square btn-ghost tooltip tooltip-bottom" data-tip="删除线">
    <span class="icon-[lucide--strikethrough] text-lg"></span>
  </button>
  <button type="button" data-cmd="underline" class="btn btn-sm btn-square btn-ghost tooltip tooltip-bottom" data-tip="下划线">
    <span class="icon-[lucide--underline] text-lg"></span>
  </button>
  <div class="w-px h-6 bg-base-300 mx-1"></div>

  <button type="button" data-cmd="alignLeft" class="btn btn-sm btn-square btn-ghost tooltip tooltip-bottom" data-tip="左对齐">
    <span class="icon-[lucide--text-align-start] text-lg"></span>
  </button>
  <button type="button" data-cmd="alignCenter" class="btn btn-sm btn-square btn-ghost tooltip tooltip-bottom" data-tip="居中对齐">
    <span class="icon-[lucide--text-align-center] text-lg"></span>
  </button>
  <button type="button" data-cmd="alignRight" class="btn btn-sm btn-square btn-ghost tooltip tooltip-bottom" data-tip="右对齐">
    <span class="icon-[lucide--text-align-end] text-lg"></span>
  </button>
  <button type="button" data-cmd="alignJustify" class="btn btn-sm btn-square btn-ghost tooltip tooltip-bottom" data-tip="两端对齐">
    <span class="icon-[lucide--text-align-justify] text-lg"></span>
  </button>
  <div class="w-px h-6 bg-base-300 mx-1"></div>

  <button type="button" data-cmd="link" class="btn btn-sm btn-square btn-ghost tooltip tooltip-bottom" data-tip="插入链接">
    <span class="icon-[lucide--link] text-lg"></span>
  </button>
  <button type="button" data-cmd="image" class="btn btn-sm btn-square btn-ghost tooltip tooltip-bottom" data-tip="插入图片">
    <span class="icon-[lucide--image] text-lg"></span>
  </button>
  <button type="button" data-cmd="video" class="btn btn-sm btn-square btn-ghost tooltip tooltip-bottom" data-tip="插入视频">
    <span class="icon-[lucide--video] text-lg"></span>
  </button>
  <div class="w-px h-6 bg-base-300 mx-1"></div>

  <button type="button" data-cmd="search" class="btn btn-sm btn-square btn-ghost tooltip tooltip-bottom" data-tip="查找替换">
    <span class="icon-[lucide--search] text-lg"></span>
  </button>
  <button type="button" data-cmd="format" class="btn btn-sm btn-ghost px-2 text-xs whitespace-nowrap tooltip tooltip-bottom" data-tip="一键排版">
    一键排版
  </button>
  <button type="button" data-cmd="source" class="btn btn-sm btn-square btn-ghost tooltip tooltip-bottom" data-tip="源代码">
    <span class="icon-[lucide--file-code] text-lg"></span>
  </button>
  <button type="button" data-cmd="fullscreen" class="btn btn-sm btn-square btn-ghost tooltip tooltip-bottom" data-tip="全屏">
    <span class="icon-[lucide--maximize] text-lg"></span>
  </button>
</div>`;

// [修复] 缓存按钮列表,避免每次 transaction 调 querySelectorAll
const buttonCache = new WeakMap();
// [修复] 缓存 undo/redo 按钮,避免每次 transaction 调 querySelector
const undoRedoCache = new WeakMap();

/**
 * 构建工具栏
 * @param {Editor|(() => Editor)} editorOrGetter - Editor 实例或返回 Editor 的 getter
 * @param {Object} handlers
 */
export function buildToolbar(editorOrGetter, handlers) {
  const getEditor =
    typeof editorOrGetter === "function"
      ? editorOrGetter
      : () => editorOrGetter;

  const { el: toolbar } = parseTemplate(TOOLBAR_HTML);

  // 缓存按钮列表
  buttonCache.set(toolbar, [...toolbar.querySelectorAll("button[data-cmd]")]);
  // [修复] 同时缓存 undo/redo 按钮
  undoRedoCache.set(toolbar, {
    undoBtn: toolbar.querySelector('button[data-cmd="undo"]'),
    redoBtn: toolbar.querySelector('button[data-cmd="redo"]'),
  });

  toolbar.addEventListener("mousedown", (event) => {
    if (event.target.closest("button[data-cmd]")) {
      event.preventDefault();
    }
  });

  toolbar.addEventListener("click", (event) => {
    const editor = getEditor();
    if (!editor) return;
    const btn = event.target.closest("button[data-cmd]");
    if (!btn) return;
    event.preventDefault();

    const cmd = btn.dataset.cmd;
    if (COMMANDS[cmd]) {
      COMMANDS[cmd](editor);
      return;
    }
    if (HANDLER_DISPATCH[cmd]) {
      HANDLER_DISPATCH[cmd](handlers);
      return;
    }
  });

  return toolbar;
}

/**
 * 更新按钮高亮状态
 * [修复] 从 WeakMap 读取缓存的按钮列表,不再每次调 querySelectorAll
 */
export function updateToolbarState(editor, toolbarEl) {
  let buttons = buttonCache.get(toolbarEl);
  if (!buttons) {
    buttons = [...toolbarEl.querySelectorAll("button[data-cmd]")];
    buttonCache.set(toolbarEl, buttons);
  }

  for (const btn of buttons) {
    const cmd = btn.dataset.cmd;
    const active = ACTIVE_CHECKS[cmd] ? ACTIVE_CHECKS[cmd](editor) : false;
    btn.classList.toggle("btn-neutral", active);
    btn.classList.toggle("btn-ghost", !active);
  }
}

/**
 * 更新 undo/redo 禁用状态
 * [修复] 从 WeakMap 读取缓存的按钮引用,不再每次调 querySelector
 */
export function updateHistoryState(editor, toolbarEl) {
  let { undoBtn, redoBtn } = undoRedoCache.get(toolbarEl) || {};
  if (!undoBtn) {
    undoBtn = toolbarEl.querySelector('button[data-cmd="undo"]');
    redoBtn = toolbarEl.querySelector('button[data-cmd="redo"]');
    undoRedoCache.set(toolbarEl, { undoBtn, redoBtn });
  }
  const canUndo = undoBtn ? editor.can().undo() : false;
  const canRedo = redoBtn ? editor.can().redo() : false;
  if (undoBtn) undoBtn.disabled = !canUndo;
  if (redoBtn) redoBtn.disabled = !canRedo;
}
