import { Node, mergeAttributes } from "@tiptap/core";

/**
 * Iframe 嵌入节点扩展
 * 用于嵌入 YouTube、Bilibili、Vimeo 等视频平台
 */
export const Iframe = Node.create({
  name: "iframe",
  group: "block",
  atom: true,
  draggable: true,

  addAttributes() {
    return {
      src: {
        default: null,
      },
      width: {
        default: "100%",
      },
      height: {
        default: "315",
      },
      frameborder: {
        default: "0",
      },
      allowfullscreen: {
        default: true,
      },
      title: {
        default: "嵌入视频",
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: "iframe",
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "div",
      { class: "iframe-wrapper", "data-type": "iframe" },
      [
        "iframe",
        mergeAttributes(HTMLAttributes, {
          allowfullscreen: HTMLAttributes.allowfullscreen ? "true" : undefined,
        }),
      ],
    ];
  },

  addCommands() {
    return {
      setIframe:
        (options: { src: string; width?: string; height?: string }) =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs: options,
          });
        },
    };
  },
});

// 类型扩展声明
declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    iframe: {
      setIframe: (options: {
        src: string;
        width?: string;
        height?: string;
      }) => ReturnType;
    };
  }
}
