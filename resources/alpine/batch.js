/**
 * 列表批量操作 Alpine 组件
 * - batchCopyLinks：表头 checkbox 全选/反选 + 复制勾选行链接
 */
import Alpine from "alpinejs";

Alpine.data("batchCopyLinks", () => ({
  /** 表头 checkbox 变化时同步所有行 checkbox 的选中态 */
  toggleAll(event) {
    const checked = event.target.checked;
    this.$root.querySelectorAll('tbody input[type="checkbox"][data-href]').forEach((box) => {
      box.checked = checked;
    });
  },

  /** 收集勾选行的链接并写入剪贴板 */
  copyLinks() {
    this._copySelected((box) => box.dataset.href, "链接");
  },

  /** 收集勾选行的 "栏目路径 + 链接" (tab 分隔) 并写入剪贴板 */
  copyLinksWithCategory() {
    this._copySelected(
      (box) => [box.dataset.category, box.dataset.href].filter(Boolean).join("\t"),
      "栏目+链接"
    );
  },

  /** 公共: 收集勾选行 → 格式化 → 写剪贴板 → toast */
  _copySelected(format, label) {
    const boxes = Array.from(
      this.$root.querySelectorAll('tbody input[type="checkbox"][data-href]:checked')
    );
    if (boxes.length === 0) {
      document.body.dispatchEvent(
        new CustomEvent("showToast", {
          detail: { type: "error", message: "未选中任何文章" },
        })
      );
      return;
    }

    this._writeClipboard(boxes.map(format).join("\n"))
      .then(() => {
        document.body.dispatchEvent(
          new CustomEvent("showToast", {
            detail: { type: "success", message: `已复制 ${boxes.length} 个${label}` },
          })
        );
      })
      .catch(() => {
        document.body.dispatchEvent(
          new CustomEvent("showToast", {
            detail: { type: "error", message: "复制失败" },
          })
        );
      });
  },

  /**
   * 写剪贴板: 优先 Async Clipboard API(https/localhost, 异步不阻塞),
   * 不存在或失败时降级 execCommand('copy')(http 内网等非 secure context,
   * navigator.clipboard 为 undefined 的唯一可用方案)。
   */
  async _writeClipboard(text) {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return;
    }
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand("copy");
    ta.remove();
    if (!ok) throw new Error("复制失败");
  },
}));
