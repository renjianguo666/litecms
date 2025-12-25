import StarterKit from "@tiptap/starter-kit";
import TextAlign from "@tiptap/extension-text-align";
import { TextStyle } from "@tiptap/extension-text-style";
import Color from "@tiptap/extension-color";
import Highlight from "@tiptap/extension-highlight";
import Image from "@tiptap/extension-image";
import Placeholder from "@tiptap/extension-placeholder";
import CharacterCount from "@tiptap/extension-character-count";

import { Video } from "./video-node";
import { Iframe } from "./iframe-node";

/**
 * 扩展配置选项
 */
interface ExtensionOptions {
  /** 占位符文本 */
  placeholder?: string;
  /** 字符数限制 */
  characterLimit?: number;
}

/**
 * 获取默认扩展配置
 */
export function getDefaultExtensions(options?: ExtensionOptions) {
  return [
    StarterKit.configure({
      heading: {
        levels: [1, 2, 3, 4, 5, 6],
      },
    }),
    TextAlign.configure({
      types: ["heading", "paragraph"],
    }),
    TextStyle,
    Color,
    Highlight.configure({
      multicolor: true,
    }),
    Image.configure({
      inline: true,
      resize: {
        enabled: true,
        alwaysPreserveAspectRatio: true,
      },
    }),
    Video,
    Iframe,
    Placeholder.configure({
      placeholder: options?.placeholder || "请输入内容...",
    }),
    CharacterCount.configure({
      limit: options?.characterLimit,
    }),
  ];
}

export default getDefaultExtensions;
