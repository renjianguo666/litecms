/**
 * 布局相关 Alpine 组件
 * - sidebarState：侧边栏展开/收起状态（桌面收起 + 移动端遮罩）
 * - fullscreenToggle：全屏切换
 * - navMenu：菜单高亮（跟随 htmx 路由变化）
 */
import Alpine from "alpinejs";

// ---------- 侧边栏 / 布局状态 ----------
Alpine.data("sidebarState", () => ({
  isDesktop: window.innerWidth >= 1024,
  sidebarCollapse: false,
  sidebarOpen: false,
  _bodyClassesApplied: false,

  init() {
    requestAnimationFrame(() => {
      this._bodyClassesApplied = true;
    });
  },

  toggle() {
    if (this.isDesktop) {
      this.sidebarCollapse = !this.sidebarCollapse;
    } else {
      this.sidebarOpen = !this.sidebarOpen;
    }
  },

  handleResize() {
    this.isDesktop = window.innerWidth >= 1024;
    if (this.isDesktop) this.sidebarOpen = false;
  },

  get bodyClasses() {
    if (!this._bodyClassesApplied) return {};
    return {
      "sidebar-collapse": this.sidebarCollapse,
      "sidebar-open": this.sidebarOpen,
    };
  },
}));

// ---------- Header 全屏切换按钮 ----------
Alpine.data("fullscreenToggle", () => ({
  isFullscreen: false,
  toggle() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      this.isFullscreen = true;
    } else {
      document.exitFullscreen();
      this.isFullscreen = false;
    }
  },
}));

// ---------- 侧边栏菜单高亮 ----------
Alpine.data("navMenu", () => ({
  currentPath: window.location.pathname,

  init() {
    const syncPath = () => {
      this.currentPath = window.location.pathname;
    };
    window.addEventListener("htmx:pushed-into-history", syncPath);
    window.addEventListener("htmx:replace-url", syncPath);
    window.addEventListener("popstate", syncPath);
  },

  navigate(path) {
    this.currentPath = path;
  },

  isActive(path, exact = false) {
    if (exact) {
      return this.currentPath === path || this.currentPath === `${path}/`;
    }
    return this.currentPath.startsWith(path);
  },
}));
