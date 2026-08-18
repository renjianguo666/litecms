/**
 * 模板工具:解析 HTML 字符串,返回根元素 + data-ref 引用映射
 *
 * @param {string} html
 * @returns {{ el: HTMLElement, refs: Record<string, HTMLElement> }}
 */
export function parseTemplate(html) {
  const tpl = document.createElement("template");
  tpl.innerHTML = html;
  const frag = tpl.content.cloneNode(true);
  const el = frag.firstElementChild;
  if (!el) {
    throw new Error("[LitecmsEditor] 模板首字符不是元素: " + html);
  }

  const refs = {};
  el.querySelectorAll("[data-ref]").forEach((node) => {
    refs[node.dataset.ref] = node;
  });
  return { el, refs };
}

/**
 * 创建元素辅助函数
 * @param {string} tag
 * @param {string} [className]
 * @param {string} [html]
 * @returns {HTMLElement}
 */
export function el(tag, className, html) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (html !== undefined) node.innerHTML = html;
  return node;
}
