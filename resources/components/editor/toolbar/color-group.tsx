import { For, createSignal } from "solid-js";
import type { Editor } from "@tiptap/core";
import { Palette, Highlighter } from "lucide-solid";
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from "@/components/ui/popover";
import { TEXT_COLORS, HIGHLIGHT_COLORS } from "../constants";
import { ToolbarGroup } from "./button";

/**
 * 颜色组属性
 */
export interface ColorGroupProps {
  editor: Editor;
}

/**
 * 颜色选择组（文字颜色、背景高亮）
 *
 * 提供文字颜色和背景高亮颜色选择功能。
 */
export function ColorGroup(props: ColorGroupProps) {
  const [textColorOpen, setTextColorOpen] = createSignal(false);
  const [highlightOpen, setHighlightOpen] = createSignal(false);

  return (
    <ToolbarGroup>
      {/* 文字颜色 */}
      <Popover open={textColorOpen()} onOpenChange={setTextColorOpen}>
        <PopoverTrigger
          as="button"
          class="inline-flex items-center justify-center size-8 rounded-md text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          title="文字颜色"
        >
          <Palette class="w-4 h-4" />
        </PopoverTrigger>
        <PopoverContent class="w-40 p-3">
          <div class="text-xs text-muted-foreground mb-2 font-medium">
            文字颜色
          </div>
          <div class="grid grid-cols-4 gap-1.5">
            <For each={TEXT_COLORS}>
              {(color) => (
                <button
                  type="button"
                  class="w-7 h-7 rounded border border-border hover:scale-110 hover:border-primary transition-all flex items-center justify-center"
                  style={{
                    "background-color":
                      color.value === "inherit" ? "transparent" : color.value,
                  }}
                  title={color.name}
                  onClick={() => {
                    if (color.value === "inherit") {
                      props.editor.chain().focus().unsetColor().run();
                    } else {
                      props.editor.chain().focus().setColor(color.value).run();
                    }
                    setTextColorOpen(false);
                  }}
                >
                  {color.value === "inherit" && (
                    <span class="text-xs text-muted-foreground">✕</span>
                  )}
                </button>
              )}
            </For>
          </div>
        </PopoverContent>
      </Popover>

      {/* 高亮颜色 */}
      <Popover open={highlightOpen()} onOpenChange={setHighlightOpen}>
        <PopoverTrigger
          as="button"
          class="inline-flex items-center justify-center size-8 rounded-md text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          title="背景高亮"
        >
          <Highlighter class="w-4 h-4" />
        </PopoverTrigger>
        <PopoverContent class="w-36 p-3">
          <div class="text-xs text-muted-foreground mb-2 font-medium">
            背景颜色
          </div>
          <div class="grid grid-cols-3 gap-1.5">
            <For each={HIGHLIGHT_COLORS}>
              {(color) => (
                <button
                  type="button"
                  class="w-7 h-7 rounded border border-border hover:scale-110 hover:border-primary transition-all flex items-center justify-center"
                  style={{ "background-color": color.value || "transparent" }}
                  title={color.name}
                  onClick={() => {
                    if (!color.value) {
                      props.editor.chain().focus().unsetHighlight().run();
                    } else {
                      props.editor
                        .chain()
                        .focus()
                        .toggleHighlight({ color: color.value })
                        .run();
                    }
                    setHighlightOpen(false);
                  }}
                >
                  {!color.value && (
                    <span class="text-xs text-muted-foreground">✕</span>
                  )}
                </button>
              )}
            </For>
          </div>
        </PopoverContent>
      </Popover>
    </ToolbarGroup>
  );
}

export default ColorGroup;
