import { Extension } from "@tiptap/core";
import { Plugin } from "@tiptap/pm/state";
import { uploadFile, uploadRemote } from "../utils/upload.js";

// // 转存失败占位图（灰色框 + 裂图 + 提示文字）
// const FAILED_PLACEHOLDER =
//   "data:image/svg+xml," +
//   encodeURIComponent(
//     '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="120">' +
//       '<rect width="400" height="120" fill="#f3f4f6" stroke="#e5e7eb" stroke-width="1" rx="8"/>' +
//       '<g fill="none" stroke="#9ca3af" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
//       '<path d="M180 40 L220 40 L240 70 L240 85 L160 85 L160 70 Z"/>' +
//       '<line x1="190" y1="50" x2="210" y2="70"/>' +
//       '<line x1="210" y1="50" x2="190" y2="70"/>' +
//       "</g>" +
//       '<text x="200" y="108" text-anchor="middle" fill="#9ca3af" font-size="13" font-family="sans-serif">图片转存失败，请手动上传</text>' +
//       "</svg>",
//     );

// 转存失败占位图
const FAILED_PLACEHOLDER =
  "data:image/svg+xml," +
  encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="180">' +
      '<rect width="480" height="180" fill="#f8f9fa" stroke="#e9ecef" stroke-width="1" rx="12"/>' +
      '<g transform="translate(192, 30)">' +
      '<rect x="0" y="0" width="96" height="72" rx="6" fill="#fff" stroke="#adb5bd" stroke-width="2"/>' +
      '<circle cx="26" cy="24" r="6" fill="#dee2e6"/>' +
      '<path d="M8 64 L34 40 L52 56 L70 36 L88 60 L88 68 L8 68 Z" fill="#dee2e6"/>' +
      '<line x1="14" y1="10" x2="86" y2="74" stroke="#adb5bd" stroke-width="2.5" stroke-linecap="round"/>' +
      "</g>" +
      '<text x="240" y="138" text-anchor="middle" fill="#6c757d" font-size="15" font-weight="500" font-family="-apple-system, BlinkMacSystemFont, sans-serif">图片转存失败</text>' +
      '<text x="240" y="160" text-anchor="middle" fill="#adb5bd" font-size="12" font-family="-apple-system, BlinkMacSystemFont, sans-serif">请选中此图，点击工具栏「插入图片」重新上传</text>' +
      "</svg>",
  );


export const ClipboardImage = Extension.create({
  name: "clipboardImage",

  addProseMirrorPlugins() {
    const { uploadUrl, skipOrigins = [] } = this.options;
    const editor = this.editor;

    return [
      new Plugin({
        props: {
          handlePaste(view, event) {
            const items = event.clipboardData?.items;
            if (!items) return false;

            // 1. 粘贴图片文件 -> 上传,失败插入占位图
            for (const item of items) {
              if (item.type.startsWith("image/")) {
                const file = item.getAsFile();
                if (file) {
                  event.preventDefault();
                  uploadFile(file, uploadUrl).then(
                    (url) => insertImage(view, url),
                    () => insertImage(view, FAILED_PLACEHOLDER),
                  );
                  return true;
                }
              }
            }

            // 2. 粘贴 HTML 含外链 img -> 立即插入,异步转存,失败替换占位图
            const html = event.clipboardData?.getData("text/html");
            if (html && html.includes("<img")) {
              event.preventDefault();
              localizeAndInsert(view, html, uploadUrl, editor, skipOrigins);
              return true;
            }

            return false;
          },

          handleDrop(view, event) {
            const files = event.dataTransfer?.files;
            if (!files) return false;

            for (const file of files) {
              if (file.type.startsWith("image/")) {
                event.preventDefault();
                uploadFile(file, uploadUrl).then(
                  (url) => insertImage(view, url),
                  () => insertImage(view, FAILED_PLACEHOLDER),
                );
                return true;
              }
            }
            return false;
          },
        },
      }),
    ];
  },
});

// 是否需要转存:相对路径 / data: / 本站域名 / CDN 域名 都跳过
function shouldLocalize(src, skipOrigins) {
  if (!src) return false;
  if (src.startsWith("/") || src.startsWith("data:")) return false;
  const all = [location.origin, ...skipOrigins];
  for (const origin of all) {
    if (origin && src.startsWith(origin)) return false;
  }
  return src.startsWith("http://") || src.startsWith("https://");
}

function insertImage(view, src) {
  const node = view.state.schema.nodes.image.create({ src });
  view.dispatch(view.state.tr.replaceSelectionWith(node));
}

// 立即插入内容,再异步转存外链图片(知乎模式)
function localizeAndInsert(view, html, uploadUrl, editor, skipOrigins) {
  // 1. 立即插入(带原始外链 src,用户马上看到内容)
  const dom = new DOMParser().parseFromString(html, "text/html");
  editor.chain().focus().insertContent(dom.body.innerHTML).run();

  // 2. 异步转存:扫描文档外链图片,逐个上传替换 src
  if (!uploadUrl) return;
  const { doc, schema } = view.state;
  const seen = new Set();

  doc.descendants((node) => {
    if (node.type === schema.nodes.image) {
      const src = node.attrs.src || "";
      if (shouldLocalize(src, skipOrigins) && !seen.has(src)) {
        seen.add(src);
        uploadRemote(src, uploadUrl).then(
          (newUrl) => replaceImageSrc(view, src, newUrl),
          () => replaceImageSrc(view, src, FAILED_PLACEHOLDER),
        );
      }
    }
    return true;
  });
}

// 找到 src 等于 oldSrc 的图片节点,替换成 newUrl
function replaceImageSrc(view, oldSrc, newUrl) {
  const state = view.state;
  const positions = [];
  state.doc.descendants((node, pos) => {
    if (node.type.name === "image" && node.attrs.src === oldSrc) {
      positions.push(pos);
    }
    return true;
  });
  if (positions.length === 0) return;
  positions.sort((a, b) => b - a);
  let tr = state.tr;
  for (const pos of positions) {
    const node = state.doc.nodeAt(pos);
    if (node) {
      tr = tr.setNodeMarkup(pos, undefined, { ...node.attrs, src: newUrl });
    }
  }
  view.dispatch(tr);
}
