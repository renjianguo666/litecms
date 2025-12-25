import { createSignal, type Accessor, onMount, onCleanup } from "solid-js";
import type { Editor } from "@tiptap/core";
import { ArrowUp, ArrowDown, X } from "lucide-solid";
import { Button } from "@/components/ui/button";
import { inputClass as baseInputClass } from "../utils/styles";

interface SearchPanelProps {
  editor: Accessor<Editor | null>;
  onClose: () => void;
}

/**
 * 查找替换面板组件
 * 固定在编辑器内容区顶部，不随内容滚动
 * 支持拖拽移动
 */
export function SearchPanel(props: SearchPanelProps) {
  const [searchText, setSearchText] = createSignal("");
  const [replaceText, setReplaceText] = createSignal("");
  const [matchCount, setMatchCount] = createSignal(0);
  const [currentMatch, setCurrentMatch] = createSignal(0);

  // 拖拽状态
  const [position, setPosition] = createSignal({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = createSignal(false);
  const [dragOffset, setDragOffset] = createSignal({ x: 0, y: 0 });

  let searchInputRef: HTMLInputElement | undefined;
  let panelRef: HTMLDivElement | undefined;

  const editor = () => props.editor();

  // 输入框样式（基于共享样式调整高度）
  const inputClass = baseInputClass.replace("h-10", "h-8");

  // 自动聚焦
  onMount(() => {
    setTimeout(() => searchInputRef?.focus(), 50);
  });

  // 拖拽处理
  const handleMouseDown = (e: MouseEvent) => {
    if (!panelRef) return;

    setIsDragging(true);
    const rect = panelRef.getBoundingClientRect();
    setDragOffset({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });

    e.preventDefault();
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging() || !panelRef) return;

    const panelRect = panelRef.getBoundingClientRect();

    // 计算新位置（相对于视口）
    let newX = e.clientX - dragOffset().x;
    let newY = e.clientY - dragOffset().y;

    // 限制在视口内
    newX = Math.max(0, Math.min(newX, window.innerWidth - panelRect.width));
    newY = Math.max(0, Math.min(newY, window.innerHeight - panelRect.height));

    setPosition({ x: newX, y: newY });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // 注册全局鼠标事件
  onMount(() => {
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
  });

  onCleanup(() => {
    document.removeEventListener("mousemove", handleMouseMove);
    document.removeEventListener("mouseup", handleMouseUp);
  });

  // 计算面板样式
  const panelStyle = () => {
    const pos = position();
    if (pos.x === 0 && pos.y === 0) {
      // 初始位置：右上角（相对定位）
      return {};
    }
    // 拖拽后使用固定定位
    return {
      position: "fixed" as const,
      left: `${pos.x}px`,
      top: `${pos.y}px`,
      right: "auto",
    };
  };

  // 统计匹配数量
  const countMatches = () => {
    const ed = editor();
    if (!ed) return;

    const search = searchText();
    if (!search) {
      setMatchCount(0);
      setCurrentMatch(0);
      return;
    }

    const content = ed.getText();
    const searchLower = search.toLowerCase();
    const contentLower = content.toLowerCase();

    let count = 0;
    let pos = 0;
    while ((pos = contentLower.indexOf(searchLower, pos)) !== -1) {
      count++;
      pos += searchLower.length;
    }
    setMatchCount(count);
  };

  // 查找下一个
  const findNext = () => {
    const ed = editor();
    if (!ed) return;

    const search = searchText();
    if (!search) return;

    const content = ed.getText();
    const selection = ed.state.selection;
    const searchLower = search.toLowerCase();
    const contentLower = content.toLowerCase();

    const startPos = selection.to;
    let index = contentLower.indexOf(searchLower, startPos);

    if (index === -1) {
      index = contentLower.indexOf(searchLower);
    }

    if (index !== -1) {
      ed.chain()
        .focus()
        .setTextSelection({ from: index + 1, to: index + 1 + search.length })
        .scrollIntoView()
        .run();

      // 更新当前匹配索引
      let matchIndex = 0;
      let pos = 0;
      while ((pos = contentLower.indexOf(searchLower, pos)) !== -1) {
        matchIndex++;
        if (pos === index) {
          setCurrentMatch(matchIndex);
          break;
        }
        pos += searchLower.length;
      }
    }
  };

  // 查找上一个
  const findPrev = () => {
    const ed = editor();
    if (!ed) return;

    const search = searchText();
    if (!search) return;

    const content = ed.getText();
    const selection = ed.state.selection;
    const searchLower = search.toLowerCase();
    const contentLower = content.toLowerCase();

    const endPos = Math.max(0, selection.from - 2);
    let index = contentLower.lastIndexOf(searchLower, endPos);

    if (index === -1) {
      index = contentLower.lastIndexOf(searchLower);
    }

    if (index !== -1) {
      ed.chain()
        .focus()
        .setTextSelection({ from: index + 1, to: index + 1 + search.length })
        .scrollIntoView()
        .run();

      // 更新当前匹配索引
      let matchIndex = 0;
      let pos = 0;
      while ((pos = contentLower.indexOf(searchLower, pos)) !== -1) {
        matchIndex++;
        if (pos === index) {
          setCurrentMatch(matchIndex);
          break;
        }
        pos += searchLower.length;
      }
    }
  };

  // 替换当前
  const replaceCurrent = () => {
    const ed = editor();
    if (!ed) return;

    const search = searchText();
    const replace = replaceText();
    if (!search) return;

    const { from, to } = ed.state.selection;
    const selectedText = ed.state.doc.textBetween(from, to, "");

    if (selectedText.toLowerCase() === search.toLowerCase()) {
      ed.chain().focus().deleteSelection().insertContent(replace).run();

      countMatches();
      findNext();
    } else {
      findNext();
    }
  };

  // 全部替换
  const replaceAll = () => {
    const ed = editor();
    if (!ed) return;

    const search = searchText();
    const replace = replaceText();
    if (!search) return;

    const html = ed.getHTML();
    const regex = new RegExp(
      search.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"),
      "gi",
    );
    const newHtml = html.replace(regex, replace);

    ed.chain().focus().setContent(newHtml).run();

    countMatches();
  };

  const handleClose = () => {
    props.onClose();
    // 聚焦回编辑器
    editor()?.commands.focus();
  };

  return (
    <div
      ref={panelRef}
      class="absolute top-2 right-2 z-50 bg-card border border-border rounded-lg shadow-lg p-4 w-80"
      style={panelStyle()}
    >
      {/* 标题栏 - 可拖拽 */}
      <div
        class="flex items-center justify-between mb-4 cursor-move select-none"
        onMouseDown={handleMouseDown}
      >
        <h3 class="font-semibold text-base">查找和替换</h3>
        <button
          type="button"
          class="inline-flex items-center justify-center size-6 rounded-md text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring cursor-pointer"
          onClick={handleClose}
          onMouseDown={(e) => e.stopPropagation()}
          title="关闭 (Esc)"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      {/* 查找输入框 */}
      <div class="space-y-3">
        <div class="space-y-1.5">
          <label for="editor-search-input" class="text-sm font-medium">
            寻找
          </label>
          <div class="flex items-center gap-2">
            <input
              ref={searchInputRef}
              type="text"
              id="editor-search-input"
              name="editor-search-input"
              class={`${inputClass} flex-1`}
              placeholder=""
              value={searchText()}
              onInput={(e) => {
                setSearchText(e.currentTarget.value);
                countMatches();
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  e.shiftKey ? findPrev() : findNext();
                }
                if (e.key === "Escape") {
                  handleClose();
                }
              }}
            />
            <button
              type="button"
              class="inline-flex items-center justify-center size-8 rounded-md text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50"
              onClick={findPrev}
              title="上一个 (Shift+Enter)"
              disabled={matchCount() === 0}
            >
              <ArrowUp class="w-4 h-4" />
            </button>
            <button
              type="button"
              class="inline-flex items-center justify-center size-8 rounded-md text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50"
              onClick={findNext}
              title="下一个 (Enter)"
              disabled={matchCount() === 0}
            >
              <ArrowDown class="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* 替换输入框 */}
        <div class="space-y-1.5">
          <label for="editor-replace-input" class="text-sm font-medium">
            替换为
          </label>
          <input
            type="text"
            id="editor-replace-input"
            name="editor-replace-input"
            class={`${inputClass} w-full`}
            placeholder=""
            value={replaceText()}
            onInput={(e) => setReplaceText(e.currentTarget.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                replaceCurrent();
              }
              if (e.key === "Escape") {
                handleClose();
              }
            }}
          />
        </div>
      </div>

      {/* 底部按钮 */}
      <div class="flex items-center justify-end gap-2 mt-4 pt-3 border-t border-border">
        <span class="text-xs text-muted-foreground mr-auto">
          {matchCount() > 0
            ? `${currentMatch()} / ${matchCount()} 个结果`
            : "无结果"}
        </span>
        <Button
          variant="ghost"
          size="sm"
          onClick={findNext}
          disabled={matchCount() === 0}
        >
          寻找
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={replaceCurrent}
          disabled={matchCount() === 0}
        >
          替换
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={replaceAll}
          disabled={matchCount() === 0}
        >
          替换全部
        </Button>
      </div>
    </div>
  );
}
