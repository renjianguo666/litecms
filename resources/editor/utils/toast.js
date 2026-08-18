/**
 * 轻量 toast 提示,替代 alert
 * [安全] 用 textContent 而非 innerHTML,防止服务端返回内容注入
 * [位置] daisyUI toast-center (顶部水平居中),多个 toast 自动堆叠
 * @param {string} message
 * @param {"info"|"success"|"error"|"warning"} type
 */
export function toast(message, type = "info") {
  const alertClass =
    {
      info: "alert-info",
      success: "alert-success",
      error: "alert-error",
      warning: "alert-warning",
    }[type] || "alert-info";

  // 单例 toast 容器(daisyUI toast 组件,水平居中,顶部)
  let container = document.getElementById("litecms-toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "litecms-toast-container";
    container.className = "toast toast-top toast-center z-[100]";
    document.body.appendChild(container);
  }

  const t = document.createElement("div");
  t.className = `alert ${alertClass} shadow-lg max-w-sm`;
  // [安全] 用 textContent 避免 XSS
  const span = document.createElement("span");
  span.textContent = message;
  t.appendChild(span);
  t.style.transition = "opacity 0.3s, transform 0.3s";
  t.style.opacity = "0";
  t.style.transform = "translateY(-8px)";
  // 上限保护:超过 3 条时移除最早的,避免无限堆叠
  while (container.children.length >= 3) {
    container.firstChild.remove();
  }
  container.appendChild(t);

  // 入场动画
  requestAnimationFrame(() => {
    t.style.opacity = "1";
    t.style.transform = "translateY(0)";
  });

  // 自动消失
  setTimeout(() => {
    t.style.opacity = "0";
    t.style.transform = "translateY(-8px)";
    setTimeout(() => {
      t.remove();
      // 容器空了就移除,避免占位
      if (container.children.length === 0) {
        container.remove();
      }
    }, 300);
  }, 2500);
}
