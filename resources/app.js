/**
 * LiteCMS 全局 Alpine.js 组件
 * ESM 打包入口：按域拆分到 alpine/，这里只做 import 聚合 + Alpine.start() + 非 Alpine 全局逻辑
 */

import Alpine from "alpinejs";

// 按域导入 Alpine 组件（各自注册 Alpine.data / Alpine.store）
import "./alpine/forms.js";        // articleTags store / combobox / coverPicker
import "./alpine/layout.js";       // sidebarState / fullscreenToggle / navMenu
import "./alpine/feedback.js";     // toastManager
import "./alpine/datetime.js";  // initVcDateTimePickers（含自启动）
import "./alpine/permissions.js";
import "./alpine/batch.js";        // batchCopyLinks：列表全选/反选 + 批量复制链接

// ---------- 启动 Alpine ----------
window.Alpine = Alpine;
Alpine.start();

// ---------- 非 Alpine 的全局逻辑：CSRF / htmx 事件 ----------
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
}

document.body.addEventListener("htmx:configRequest", (evt) => {
  if (evt.detail.method !== "GET") {
    const freshToken = getCookie("csrftoken");
    if (freshToken) evt.detail.headers["X-CSRFToken"] = freshToken;
  }
});

document.body.addEventListener("showToast", (e) => {
  if (e.detail.type === "success") {
    const container = document.getElementById("dialog-container");
    const dialog = container?.querySelector("dialog");
    if (dialog) dialog.close();
    if (container) container.innerHTML = "";
  }
});
