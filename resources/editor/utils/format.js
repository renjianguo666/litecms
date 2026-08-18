/**
 * HTML 格式化工具函数
 * 参考 seoserp.cn / ueditor 一键排版的常规做法
 * 设计原则:安全第一,绝不误杀有内容的段落或功能性属性
 *
 * 流程:
 *   1. 清理空段、空白段、纯 <br> 段(保护锚点/媒体)
 *   2. 拆分媒体:文字+媒体混排 -> 拆成独立段;多媒体同段 -> 每媒体一段
 *   3. 清理属性(白名单制,保留功能性属性)
 *   4. 识别图注(前一个 p 是纯媒体块 + 当前 p 是短文本/带引导词)
 *   5. 段落首行缩进 / 媒体居中 / 标题居中 / 图注居中
 */

/* ---------- 1. 空段清理 ---------- */

export function removeEmptyParagraphs(html) {
  if (!html) return "";
  const container = document.createElement("div");
  container.innerHTML = html;

  const paragraphs = [...container.querySelectorAll("p")];
  for (let i = paragraphs.length - 1; i >= 0; i--) {
    const p = paragraphs[i];
    if (p.querySelector("img, video, iframe, hr, embed")) continue;
    if (p.querySelector("a")) continue;
    const text = (p.textContent || "").replace(/&nbsp;/g, " ").trim();
    if (text === "") p.remove();
  }

  return container.innerHTML;
}

/* ---------- 2. 媒体拆分 ---------- */

function isMediaNode(node) {
  return (
    node.nodeType === 1 &&
    ["IMG", "VIDEO", "IFRAME", "EMBED"].includes(node.tagName)
  );
}

export function splitImages(html) {
  if (!html) return "";
  const container = document.createElement("div");
  container.innerHTML = html;

  const paragraphs = [...container.querySelectorAll("p")];
  paragraphs.forEach((p) => {
    const mediaNodes = [...p.querySelectorAll("img, video, iframe, embed")];
    if (mediaNodes.length === 0) return;

    const hasText = (p.textContent || "").trim().length > 0;

    if (!hasText) {
      if (mediaNodes.length > 1) {
        mediaNodes.forEach((media) => {
          const newP = document.createElement("p");
          newP.appendChild(media.cloneNode(true));
          p.parentNode.insertBefore(newP, p);
        });
        p.remove();
      }
      return;
    }

    const fragments = [];
    let current = null;
    [...p.childNodes].forEach((node) => {
      const type = isMediaNode(node) ? "media" : "text";
      if (!current || current.type !== type) {
        current = { type, nodes: [] };
        fragments.push(current);
      }
      current.nodes.push(node);
    });

    const newParagraphs = fragments.map((frag) => {
      const newP = document.createElement("p");
      frag.nodes.forEach((n) => newP.appendChild(n.cloneNode(true)));
      return newP;
    });

    let insertAfter = p;
    newParagraphs.forEach((newP) => {
      insertAfter.parentNode.insertBefore(newP, insertAfter.nextSibling);
      insertAfter = newP;
    });
    p.remove();
  });

  return container.innerHTML;
}

/* ---------- 3. 属性清理 ---------- */

const KEEP_ATTRS = {
  "*": ["src", "href", "alt", "title", "width", "height", "colspan", "rowspan"],
  a: ["href", "title", "target", "rel"],
  img: ["src", "srcset", "alt", "title", "width", "height", "loading", "sizes"],
  iframe: [
    "src",
    "width",
    "height",
    "frameborder",
    "allow",
    "allowfullscreen",
    "loading",
  ],
  video: [
    "src",
    "poster",
    "controls",
    "autoplay",
    "loop",
    "muted",
    "preload",
    "width",
    "height",
  ],
  audio: ["src", "controls", "autoplay", "loop", "muted", "preload"],
  table: ["border", "cellpadding", "cellspacing"],
  ol: ["start", "reversed", "type"],
  ul: ["type"],
  col: ["span", "width"],
  colgroup: ["span"],
};

// [修复] Tiptap TextAlign 扩展将段落对齐存储为 inline style:
//   <p style="text-align: center">
// cleanAttributes 必须保留 text-align,否则用户设置的对齐在
// 保存(syncToInputImmediate)、源代码视图(source-dialog)、getHTML() 时全部丢失。
// 其他 style 属性(color/font-size/background 等)仍然全部删除。
const SAFE_INLINE_STYLES = ["text-align"];

function filterStyle(styleValue) {
  const styles = styleValue
    .split(";")
    .map((s) => s.trim())
    .filter(Boolean);
  const kept = styles.filter((decl) => {
    const prop = decl.split(":")[0].trim().toLowerCase();
    return SAFE_INLINE_STYLES.includes(prop);
  });
  return kept.join("; ");
}

export function cleanAttributes(html) {
  if (!html) return "";
  const container = document.createElement("div");
  container.innerHTML = html;

  container.querySelectorAll("*").forEach((el) => {
    const tag = el.tagName.toLowerCase();
    const keep = new Set([
      ...(KEEP_ATTRS["*"] || []),
      ...(KEEP_ATTRS[tag] || []),
    ]);

    [...el.attributes].forEach((attr) => {
      const name = attr.name.toLowerCase();
      if (name.startsWith("on")) {
        el.removeAttribute(attr.name);
        return;
      }
      if (keep.has(name)) return;
      if (
        name.startsWith("data-pm-") ||
        name === "contenteditable" ||
        name === "draggable"
      ) {
        el.removeAttribute(attr.name);
        return;
      }
      if (name === "style") {
        const safeStyle = filterStyle(el.style.cssText);
        if (safeStyle) {
          el.setAttribute("style", safeStyle);
        } else {
          el.removeAttribute(attr.name);
        }
        return;
      }
      if (name === "class") {
        el.removeAttribute(attr.name);
        return;
      }
      el.removeAttribute(attr.name);
    });
  });

  return container.innerHTML;
}

/* ---------- 4. 图注识别 ---------- */

// 图注判定逻辑(仅在 prevIsMedia 为真时调用):
//   Tier 1: 有图注引导词(图1/图:/注:/Fig./Figure/图片来源 等)-> ≤ 40 字
//   Tier 2: 无引导词,极短纯文本(≤ 10 字、无标点、无内联媒体/链接)
// Tier 2 的前提是前一个块是纯媒体块,所以不会误判正文中的普通短句 --
// 只有紧跟在图片/视频后面的短文本才会被识别为图注
function isCaptionText(block) {
  const text = (block.textContent || "").trim();
  if (!text) return false;

  // 排除伪标题:整段是 <strong> 或 <b> 包裹
  const onlyChild = block.children.length === 1 && block.children[0];
  const isBoldOnly =
    onlyChild &&
    (onlyChild.tagName === "STRONG" || onlyChild.tagName === "B") &&
    (onlyChild.textContent || "").trim() === text;
  if (isBoldOnly) return false;

  // Tier 1: 有图注引导词 -> ≤ 40 字即可
  if (
    /^(图\s*\d|图\s*[:：]|注\s*[:：]|Fig\.?\s*\d|Figure\s*\d|图片来源|图片说明|Caption)/i.test(
      text,
    )
  ) {
    return text.length <= 40;
  }

  // Tier 2: 无引导词,极短纯文本标签
  // 仅在前一个块是纯媒体块时触发(markImageCaptions 中的 prevIsMedia 守卫)
  if (text.length <= 10 && !/[。！？!?,，、；;:：]/.test(text)) {
    if (!block.querySelector("a, img, video, iframe")) {
      return true;
    }
  }

  return false;
}

// 纯媒体块:<p> 且只含 img/video/iframe/embed,无文字
function isPureMediaBlock(block) {
  if (block.tagName !== "P") return false;
  if (!block.querySelector("img, video, iframe, embed")) return false;
  const text = (block.textContent || "").replace(/&nbsp;/g, " ").trim();
  return text === "";
}

export function markImageCaptions(html) {
  if (!html) return "";
  const container = document.createElement("div");
  container.innerHTML = html;

  const blocks = [...container.children];
  let prevIsMedia = false;

  blocks.forEach((block) => {
    // 只有前一个块是纯媒体块时,当前短文本才可能是图注
    if (prevIsMedia && block.tagName === "P") {
      if (isCaptionText(block)) {
        block.setAttribute("data-caption", "1");
      }
    }
    prevIsMedia = isPureMediaBlock(block);
  });

  return container.innerHTML;
}

/* ---------- 5. 缩进 / 居中 ---------- */

export function addParagraphIndent(html) {
  if (!html) return "";
  const container = document.createElement("div");
  container.innerHTML = html;

  [...container.children].forEach((block) => {
    const tag = block.tagName.toLowerCase();

    if (/^h[1-6]$/.test(tag)) {
      block.style.textAlign = "center";
      return;
    }

    if (tag !== "p") return;

    if (isPureMediaBlock(block)) {
      block.style.textAlign = "center";
      return;
    }

    if (block.getAttribute("data-caption") === "1") {
      block.style.textAlign = "center";
      block.style.fontSize = "0.875em";
      block.style.color = "#6b7280";
      block.removeAttribute("data-caption");
      return;
    }

    // [修复] 用原始 textContent 检查首字符,不能用 trim() 后的值
    // trim() 会移除全角空格(U+3000),导致 startsWith("　") 永远 false,
    // 每次点击排版都重复添加 "　　",中文空格无限叠加
    const rawText = block.textContent || "";
    const text = rawText.trim();
    if (!text) return;
    if (rawText.startsWith("　")) return;

    // 优先 prepend 到已有文本节点,避免创建多余文本节点
    const firstChild = block.firstChild;
    if (firstChild && firstChild.nodeType === Node.TEXT_NODE) {
      firstChild.textContent = "　　" + firstChild.textContent;
    } else {
      block.insertAdjacentText("afterbegin", "　　");
    }
  });

  return container.innerHTML;
}

/* ---------- 6. 主入口 ---------- */

export function formatHtmlContent(html) {
  if (!html) return "";
  html = removeEmptyParagraphs(html);
  // 先清理属性再拆分媒体:确保 cloneNode 时节点已无 on*/style 残留
  html = cleanAttributes(html);
  html = splitImages(html);
  html = markImageCaptions(html);
  html = addParagraphIndent(html);
  return html;
}

/* ---------- 7. 编辑器输出清理 ---------- */

export function cleanEditorHtml(html) {
  if (!html) return "";
  return cleanAttributes(html);
}
