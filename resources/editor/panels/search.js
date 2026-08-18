import { parseTemplate } from "../utils/dom.js";

const SEARCH_HTML = `
<div class="fixed z-9999 bg-base-100 border border-base-300 rounded-box shadow-lg p-3 w-80"
  style="display:none">
  <div class="flex items-center justify-between mb-3">
    <h3 class="font-semibold cursor-move select-none" data-ref="handle">查找替换</h3>
    <button type="button" class="btn btn-sm btn-square btn-ghost" data-action="close">
      <span class="icon-[lucide--x]"></span>
    </button>
  </div>

  <div class="form-control mb-2">
    <label class="label label-text pb-1" for="editor-search-find"><span>寻找</span></label>
    <div class="flex gap-1">
      <input type="text" id="editor-search-find" name="editor-search-find"
        class="input input-sm input-bordered flex-1" data-ref="find">
      <button type="button" class="btn btn-sm btn-square btn-ghost" data-action="prev">
        <span class="icon-[lucide--arrow-up]"></span>
      </button>
      <button type="button" class="btn btn-sm btn-square btn-ghost" data-action="next">
        <span class="icon-[lucide--arrow-down]"></span>
      </button>
    </div>
  </div>

  <div class="form-control mb-3">
    <label class="label label-text pb-1" for="editor-search-replace"><span>替换为</span></label>
    <input type="text" id="editor-search-replace" name="editor-search-replace"
      class="input input-sm input-bordered w-full" data-ref="replace">
  </div>

  <div class="flex items-center justify-end gap-1 pt-2 border-t border-base-300">
    <span class="text-xs text-base-content/50 mr-auto" data-ref="count">无结果</span>
    <button type="button" class="btn btn-xs btn-ghost" data-action="next">查找</button>
    <button type="button" class="btn btn-xs btn-ghost" data-action="replace">替换</button>
    <button type="button" class="btn btn-xs btn-ghost" data-action="replace-all">替换全部</button>
  </div>
</div>`;

function getMatches(editor, term) {
  const needle = term.toLowerCase();
  const matches = [];
  if (!needle) return matches;
  editor.state.doc.descendants((node, pos) => {
    if (!node.isText || !node.text) return;
    const text = node.text.toLowerCase();
    let index = text.indexOf(needle);
    while (index !== -1) {
      matches.push({ from: pos + index, to: pos + index + term.length });
      index = text.indexOf(needle, index + Math.max(term.length, 1));
    }
  });
  return matches;
}

export function createSearchPanel(editor) {
  const { el: panel, refs } = parseTemplate(SEARCH_HTML);

  let currentIndex = -1;
  let cachedTerm = null;
  let cachedMatches = [];
  let cacheValid = false;

  function invalidateCache() {
    cacheValid = false;
  }

  function getMatchesCached() {
    const term = refs.find.value;
    if (!cacheValid || cachedTerm !== term) {
      cachedTerm = term;
      cachedMatches = getMatches(editor, term);
      cacheValid = true;
    }
    return cachedMatches;
  }

  editor.on("update", invalidateCache);

  function updateCount() {
    const matches = getMatchesCached();
    if (!refs.find.value) {
      refs.count.textContent = "";
      return;
    }
    if (!matches.length) {
      refs.count.textContent = "无结果";
      return;
    }
    refs.count.textContent = `${currentIndex + 1} / ${matches.length} 个结果`;
  }

  function findNext() {
    const matches = getMatchesCached();
    if (!matches.length) {
      currentIndex = -1;
      updateCount();
      return;
    }
    currentIndex = (currentIndex + 1) % matches.length;
    editor
      .chain()
      .focus()
      .setTextSelection(matches[currentIndex])
      .scrollIntoView()
      .run();
    updateCount();
  }

  function findPrev() {
    const matches = getMatchesCached();
    if (!matches.length) {
      currentIndex = -1;
      updateCount();
      return;
    }
    currentIndex = currentIndex <= 0 ? matches.length - 1 : currentIndex - 1;
    editor
      .chain()
      .focus()
      .setTextSelection(matches[currentIndex])
      .scrollIntoView()
      .run();
    updateCount();
  }

  function replaceOne() {
    const term = refs.find.value;
    if (!term) return;
    const replacement = refs.replace.value || "";
    const matches = getMatchesCached();
    if (!matches.length) {
      currentIndex = -1;
      updateCount();
      return;
    }
    // 基于 currentIndex 定位的 match 替换,不依赖 editor 选区状态
    // 避免用户点击别处丢失选区后替换静默失败
    if (currentIndex < 0 || currentIndex >= matches.length) {
      currentIndex = 0;
    }
    const { from, to } = matches[currentIndex];
    editor.view.dispatch(editor.state.tr.insertText(replacement, from, to));
    // [修复] 替换后 matches 数组变短,currentIndex 可能越界
    // 必须重置为 -1,findNext 会从第一个匹配开始
    invalidateCache();
    currentIndex = -1;
    findNext();
  }

  function replaceAll() {
    const term = refs.find.value;
    const replacement = refs.replace.value || "";
    const matches = getMatchesCached();
    if (!term || !matches.length) return;
    const tr = editor.state.tr;
    matches
      .slice()
      .reverse()
      .forEach((m) => tr.insertText(replacement, m.from, m.to));
    editor.view.dispatch(tr);
    currentIndex = -1;
    invalidateCache();
    refs.count.textContent = `${matches.length} 处已替换`;
  }

  // ============ 拖拽 ============
  const handle = refs.handle;
  let dragging = false;
  let offsetX = 0;
  let offsetY = 0;
  let panelWidth = 0;
  let panelHeight = 0;

  // mousemove 里不再读任何布局属性, 只做纯计算 + 写样式
  function onDragStart(e) {
      dragging = true;
      const rect = panel.getBoundingClientRect();
      offsetX = e.clientX - rect.left;
      offsetY = e.clientY - rect.top;
      panelWidth = panel.offsetWidth;   // 缓存, 之后 mousemove 复用
      panelHeight = panel.offsetHeight;
      e.preventDefault();
  }

  function onDragMove(e) {
      if (!dragging) return;
      const maxLeft = window.innerWidth - panelWidth;
      const maxTop = window.innerHeight - panelHeight;
      const left = Math.max(0, Math.min(e.clientX - offsetX, maxLeft));
      const top = Math.max(0, Math.min(e.clientY - offsetY, maxTop));
      panel.style.left = `${left}px`;
      panel.style.top = `${top}px`;
  }

  function onDragEnd() {
    dragging = false;
  }

  handle.addEventListener("mousedown", onDragStart);
  document.addEventListener("mousemove", onDragMove);
  document.addEventListener("mouseup", onDragEnd);

  // 按钮事件
  panel.addEventListener("click", (event) => {
    const btn = event.target.closest("button[data-action]");
    if (!btn) return;
    const action = btn.dataset.action;
    if (action === "close") close();
    else if (action === "next") findNext();
    else if (action === "prev") findPrev();
    else if (action === "replace") replaceOne();
    else if (action === "replace-all") replaceAll();
  });

  refs.find.addEventListener("input", () => {
    currentIndex = -1;
    invalidateCache();
    updateCount();
  });

  refs.find.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      e.shiftKey ? findPrev() : findNext();
    }
    if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      close();
    }
  });

  refs.replace.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      replaceOne();
    }
    if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      close();
    }
  });

  function getDefaultPosition() {
    const contentWrap = editor.view.dom.closest(".editor-content");
    if (!contentWrap) {
      return { left: window.innerWidth - 320 - 16, top: 80 };
    }
    const rect = contentWrap.getBoundingClientRect();
    return {
      left: Math.max(16, rect.right - 320 - 8),
      top: Math.max(16, rect.top + 8),
    };
  }

  function open() {
    const { left, top } = getDefaultPosition();
    panel.style.left = `${left}px`;
    panel.style.top = `${top}px`;
    panel.style.display = "";
    setTimeout(() => refs.find.focus(), 50);
  }

  function close() {
    panel.style.display = "none";
    editor.commands.focus();
  }

  function destroy() {
    editor.off("update", invalidateCache);
    handle.removeEventListener("mousedown", onDragStart);
    document.removeEventListener("mousemove", onDragMove);
    document.removeEventListener("mouseup", onDragEnd);
    panel.remove();
  }

  return { el: panel, open, close, destroy };
}
