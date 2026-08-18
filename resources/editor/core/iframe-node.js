import { Node, mergeAttributes } from "@tiptap/core";
import { isValidEmbedUrl, convertToEmbedUrl } from "../utils/security.js";

export const Iframe = Node.create({
  name: "iframe",
  group: "block",
  atom: true,
  draggable: true,

  addAttributes() {
    return {
      src: { default: null },
      width: { default: "100%" },
      height: { default: "315" },
      title: { default: "嵌入视频" },
    };
  },

  parseHTML() {
    return [
      {
        tag: "iframe",
        // 白名单校验 + 返回转换后的 src
        getAttrs: (el) => {
          const src = el.getAttribute("src") || "";
          if (isValidEmbedUrl(src)) return { src };
          const converted = convertToEmbedUrl(src);
          if (converted) return { src: converted };
          return false; // 拒绝非白名单 iframe
        },
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
          width: HTMLAttributes.width || "100%",
          height: HTMLAttributes.height || "315",
          // [修复] 布尔属性用空字符串,不能用 true(否则输出 allowfullscreen="true" 无效)
          allowfullscreen: "",
          loading: "lazy",
          style: "border:0; pointer-events:auto;",
        }),
      ],
    ];
  },

  // NodeView:让 iframe 内部事件不被 ProseMirror 拦截
  addNodeView() {
    return ({ node }) => {
      const dom = document.createElement("div");
      dom.className = "iframe-wrapper";
      dom.setAttribute("data-type", "iframe");
      dom.style.cssText = "position:relative; width:100%;";

      const iframe = document.createElement("iframe");
      iframe.setAttribute("src", node.attrs.src || "");
      iframe.setAttribute("width", node.attrs.width || "100%");
      iframe.setAttribute("height", node.attrs.height || "315");
      iframe.setAttribute("allowfullscreen", "");
      iframe.setAttribute("loading", "lazy");
      iframe.style.cssText = "border:0; display:block; pointer-events:auto;";
      dom.appendChild(iframe);

      return { dom };
    };
  },

  addCommands() {
    return {
      setIframe:
        (options) =>
        ({ commands }) =>
          commands.insertContent({ type: this.name, attrs: options }),
    };
  },
});

export default Iframe;
