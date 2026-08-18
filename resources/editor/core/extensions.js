import StarterKit from "@tiptap/starter-kit";
import TextAlign from "@tiptap/extension-text-align";
import Image from "@tiptap/extension-image";
import Placeholder from "@tiptap/extension-placeholder";
import CharacterCount from "@tiptap/extension-character-count";
import { Video } from "./video-node.js";
import { Iframe } from "./iframe-node.js";
import { ClipboardImage } from "./clipboard-image.js";

export function buildExtensions(options = {}) {
  return [
    StarterKit.configure({
      heading: { levels: [1, 2, 3, 4, 5, 6] },
      link: { openOnClick: false, autolink: true },
    }),
    TextAlign.configure({ types: ["heading", "paragraph"] }),
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
      placeholder: options.placeholder || "请输入内容...",
    }),
    CharacterCount.configure({ limit: options.characterLimit }),
    ClipboardImage.configure({
      uploadUrl: options.uploadUrl,
      skipOrigins: options.skipOrigins || [],
    }),
  ];
}

export default buildExtensions;
