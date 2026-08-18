import { Node, mergeAttributes } from "@tiptap/core";

export const Video = Node.create({
  name: "video",
  group: "block",
  atom: true,
  draggable: true,

  addAttributes() {
    return {
      src: { default: null },
      width: { default: "100%" },
      // [修复] 布尔属性用 per-attribute parseHTML/renderHTML
      // 旧代码默认 parseHTML 读 getAttribute("controls") 返回 "" (falsy),
      // 导致 <video controls> → controls:"" → renderHTML 删除 controls,round-trip 反转
      controls: {
        default: true,
        parseHTML: (el) => el.hasAttribute("controls"),
        renderHTML: (attrs) => (attrs.controls ? { controls: "" } : {}),
      },
      autoplay: {
        default: false,
        parseHTML: (el) => el.hasAttribute("autoplay"),
        renderHTML: (attrs) => (attrs.autoplay ? { autoplay: "" } : {}),
      },
      loop: {
        default: false,
        parseHTML: (el) => el.hasAttribute("loop"),
        renderHTML: (attrs) => (attrs.loop ? { loop: "" } : {}),
      },
      muted: {
        default: false,
        parseHTML: (el) => el.hasAttribute("muted"),
        renderHTML: (attrs) => (attrs.muted ? { muted: "" } : {}),
      },
    };
  },

  parseHTML() {
    return [{ tag: "video" }];
  },

  // [修复] 简化 renderHTML —— 布尔属性由 per-attribute renderHTML 处理,
  // HTMLAttributes 已包含正确的值,不再需要手动 forEach 转换
  renderHTML({ HTMLAttributes }) {
    return [
      "div",
      { class: "video-wrapper", "data-type": "video" },
      ["video", mergeAttributes(HTMLAttributes, { style: "display:block;" })],
    ];
  },

  addNodeView() {
    return ({ node }) => {
      const dom = document.createElement("div");
      dom.className = "video-wrapper";
      dom.setAttribute("data-type", "video");
      dom.style.cssText = "width:100%;";

      const video = document.createElement("video");
      video.setAttribute("src", node.attrs.src || "");
      video.setAttribute("width", node.attrs.width || "100%");
      video.style.cssText = "display:block; pointer-events:auto;";
      if (node.attrs.controls) video.setAttribute("controls", "");
      if (node.attrs.autoplay) video.setAttribute("autoplay", "");
      if (node.attrs.loop) video.setAttribute("loop", "");
      if (node.attrs.muted) video.setAttribute("muted", "");
      dom.appendChild(video);

      return { dom };
    };
  },

  addCommands() {
    return {
      setVideo:
        (options) =>
        ({ commands }) =>
          commands.insertContent({ type: this.name, attrs: options }),
    };
  },
});

export default Video;
