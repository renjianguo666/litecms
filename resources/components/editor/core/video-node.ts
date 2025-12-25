import { Node, mergeAttributes } from "@tiptap/core";

/**
 * 视频节点扩展
 * 用于嵌入 mp4、webm 等视频文件
 */
export const Video = Node.create({
  name: "video",
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
        default: "auto",
      },
      controls: {
        default: true,
      },
      autoplay: {
        default: false,
      },
      loop: {
        default: false,
      },
      muted: {
        default: false,
      },
    };
  },

  parseHTML() {
    return [
      {
        tag: "video",
      },
    ];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "div",
      { class: "video-wrapper", "data-type": "video" },
      [
        "video",
        mergeAttributes(HTMLAttributes, {
          controls: HTMLAttributes.controls ? "true" : undefined,
          autoplay: HTMLAttributes.autoplay ? "true" : undefined,
          loop: HTMLAttributes.loop ? "true" : undefined,
          muted: HTMLAttributes.muted ? "true" : undefined,
        }),
      ],
    ];
  },

  addCommands() {
    return {
      setVideo:
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

export default Video;
