import { createEffect, createSignal, onMount } from "solid-js";

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  onSave?: () => void;
  readonly?: boolean;
  language?: string;
}

export default function CodeEditor(props: CodeEditorProps) {
  let textareaRef: HTMLTextAreaElement | undefined;
  const [lineCount, setLineCount] = createSignal(1);

  // 更新行号
  const updateLineCount = (content: string) => {
    const lines = content.split("\n").length;
    setLineCount(lines);
  };

  // 初始化行号
  onMount(() => {
    updateLineCount(props.value);
  });

  // 当外部 value 变化时更新行号
  createEffect(() => {
    updateLineCount(props.value);
  });

  // 处理输入
  const handleInput = (e: InputEvent) => {
    const target = e.target as HTMLTextAreaElement;
    props.onChange(target.value);
    updateLineCount(target.value);
  };

  // 处理键盘事件
  const handleKeyDown = (e: KeyboardEvent) => {
    // Ctrl+S / Cmd+S 保存
    if ((e.ctrlKey || e.metaKey) && e.key === "s") {
      e.preventDefault();
      props.onSave?.();
      return;
    }

    // Tab 键插入缩进
    if (e.key === "Tab") {
      e.preventDefault();
      const target = e.target as HTMLTextAreaElement;
      const start = target.selectionStart;
      const end = target.selectionEnd;
      const value = target.value;
      const indent = "  "; // 2 空格缩进

      // 插入缩进
      const newValue =
        value.substring(0, start) + indent + value.substring(end);
      props.onChange(newValue);

      // 恢复光标位置
      requestAnimationFrame(() => {
        target.selectionStart = target.selectionEnd = start + indent.length;
      });
    }
  };

  // 同步滚动
  const handleScroll = (e: Event) => {
    const target = e.target as HTMLTextAreaElement;
    const lineNumbers = target.previousElementSibling as HTMLElement;
    if (lineNumbers) {
      lineNumbers.scrollTop = target.scrollTop;
    }
  };

  return (
    <div class="h-full flex flex-col bg-muted rounded-lg overflow-hidden border border-border">
      {/* 编辑器头部 */}
      <div class="flex items-center justify-between px-3 py-2 bg-accent/50 border-b border-border">
        <span class="text-xs text-muted-foreground font-mono">
          {props.language || "HTML / Jinja2"}
        </span>
        <div class="flex items-center gap-2 text-xs text-muted-foreground">
          <span>{lineCount()} 行</span>
          <span>•</span>
          <span>Ctrl+S 保存</span>
        </div>
      </div>

      {/* 编辑器主体 */}
      <div class="flex-1 flex overflow-hidden">
        {/* 行号 */}
        <div
          class="shrink-0 w-12 bg-accent/30 text-right pr-3 py-3 font-mono text-xs text-muted-foreground/60 select-none overflow-hidden"
          style={{ "line-height": "1.5rem" }}
        >
          {Array.from({ length: lineCount() }, (_, i) => (
            <div>{i + 1}</div>
          ))}
        </div>

        {/* 代码区域 */}
        <textarea
          id="code-editor"
          ref={textareaRef}
          value={props.value}
          onInput={handleInput}
          onKeyDown={handleKeyDown}
          onScroll={handleScroll}
          readonly={props.readonly}
          spellcheck={false}
          class="flex-1 bg-transparent resize-none p-3 font-mono text-sm leading-6 outline-none text-foreground placeholder:text-foreground/30"
          style={{
            "tab-size": "2",
            "line-height": "1.5rem",
          }}
          placeholder="在此输入模板内容..."
        />
      </div>
    </div>
  );
}
