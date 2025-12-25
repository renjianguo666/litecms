interface StatusBarProps {
  characters: number;
  words: number;
}

/**
 * 编辑器状态栏
 * 显示字数统计
 */
export function StatusBar(props: StatusBarProps) {
  return (
    <div class="flex items-center justify-end px-3 py-1.5 border-t border-border bg-muted/50 text-xs text-muted-foreground">
      <div class="flex items-center gap-4">
        <span>
          <span class="font-medium">{props.characters}</span> 字符
        </span>
        <span>
          <span class="font-medium">{props.words}</span> 字
        </span>
      </div>
    </div>
  );
}
