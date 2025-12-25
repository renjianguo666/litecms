/**
 * HTML 格式化工具函数
 */

/**
 * 清理 HTML 属性，移除不必要的 style 和 class
 */
export function cleanAttributes(html: string): string {
  // 移除空的 style 属性
  html = html.replace(/\s+style=""/g, "");
  // 移除空的 class 属性
  html = html.replace(/\s+class=""/g, "");
  // 移除 data-* 属性（编辑器内部使用）
  html = html.replace(/\s+data-[a-z-]+="[^"]*"/g, "");

  return html;
}

/**
 * 给段落添加中文首行缩进（两个全角空格）
 * 如果段落包含图片，则居中显示，不添加缩进
 */
export function addParagraphIndent(html: string): string {
  if (!html) return "";

  // 匹配 <p> 标签及其内容
  return html.replace(/<p([^>]*)>([\s\S]*?)<\/p>/g, (match, attrs, content) => {
    // 如果段落包含图片，添加居中样式，不加缩进
    if (/<img\s/.test(content)) {
      // 检查是否已有 style 属性
      if (/style\s*=/.test(attrs)) {
        // 已有 style，追加 text-align
        const newAttrs = attrs.replace(
          /style\s*=\s*["']([^"']*)["']/,
          (m: string, styles: string) => {
            if (/text-align/.test(styles)) return m;
            return `style="${styles}; text-align: center;"`;
          },
        );
        return `<p${newAttrs}>${content}</p>`;
      } else {
        // 没有 style，添加新的
        return `<p${attrs} style="text-align: center;">${content}</p>`;
      }
    }

    // 纯文本段落，添加中文首行缩进
    // 排除已经有缩进的段落（以全角空格开头）
    const trimmedContent = content.replace(/^\s*/, "");
    if (trimmedContent.startsWith("　")) {
      return match;
    }

    // 在内容开头添加两个全角空格
    return `<p${attrs}>　　${trimmedContent}</p>`;
  });
}

/**
 * 格式化 HTML 内容（一键排版）
 */
export function formatHtmlContent(html: string): string {
  if (!html) return "";

  // 1. 清理属性
  html = cleanAttributes(html);

  // 2. 给段落添加中文首行缩进
  html = addParagraphIndent(html);

  return html;
}

/**
 * 清理编辑器输出的 HTML
 * 移除编辑器添加的额外标记和属性
 */
export function cleanEditorHtml(html: string): string {
  if (!html) return "";

  // 移除编辑器特定的类
  html = html.replace(/\s+class="ProseMirror[^"]*"/g, "");

  // 移除 contenteditable 属性
  html = html.replace(/\s+contenteditable="[^"]*"/g, "");

  // 移除拖拽相关属性
  html = html.replace(/\s+draggable="[^"]*"/g, "");

  // 清理属性
  html = cleanAttributes(html);

  return html;
}
