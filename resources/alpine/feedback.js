/**
 * 反馈类 Alpine 组件
 * - toastManager：全局 toast 通知（配合后端 showToast 事件）
 */
import Alpine from "alpinejs";

// ---------- 全局 Toast 通知 ----------
Alpine.data("toastManager", () => ({
  toasts: [],

  add(detail) {
    const id = Date.now() + Math.random();
    this.toasts.push({
      id,
      message: detail.message,
      type: detail.type || "info",
    });
    setTimeout(() => {
      this.toasts = this.toasts.filter((t) => t.id !== id);
    }, 3000);
  },

  remove(id) {
    this.toasts = this.toasts.filter((t) => t.id !== id);
  },

  alertClass(type) {
    return {
      "alert-info": type === "info",
      "alert-success": type === "success",
      "alert-error": type === "error" || type === "danger",
    };
  },
}));
