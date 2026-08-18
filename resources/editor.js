/**
 * LitecmsEditor 打包入口
 * 自动扫描 [data-editor] 元素并初始化，支持 HTMX swap 后重新初始化
 */
import { createEditor } from "./editor/index.js";

function initEditors() {
  document.querySelectorAll("[data-editor]").forEach((el) => {
    if (el.__editor) return;

    let config = {};
    if (el.dataset.config) {
      try {
        config = JSON.parse(el.dataset.config);
      } catch (e) {
        console.error("[LitecmsEditor] data-config JSON 解析失败:", e);
        return;
      }
    }

    el.__editor = createEditor(el, config);
  });
}

// 首次加载
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initEditors);
} else {
  initEditors();
}

// HTMX 局部更新后重新扫描
document.body.addEventListener("htmx:afterSwap", initEditors);
