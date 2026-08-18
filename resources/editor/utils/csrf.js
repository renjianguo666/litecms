/**
 * 全局 CSRF 保护 —— 自动给非安全方法的 fetch 请求注入 X-CSRFToken header。
 *
 * Litestar CSRFConfig 默认:
 *   cookie_name = "csrftoken"
 *   header_name = "x-csrftoken"
 *   safe_methods = {GET, HEAD, OPTIONS}
 *
 * 用法:在应用入口最早处调用 `setupCsrf()` 一次即可,之后所有 fetch 自动带 token。
 * 跟 Django 的 csrf.js / Rails 的 rails-ujs 是同一个思路。
 */

const CSRF_COOKIE_NAME = "csrftoken";
const CSRF_HEADER_NAME = "X-CSRFToken";
const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

function readCookie(name) {
  const match = document.cookie.match(
    new RegExp("(?:^|;\\s*)" + name + "=([^;]+)"),
  );
  return match ? decodeURIComponent(match[1]) : "";
}

/**
 * 读取当前 CSRF token(优先 cookie,其次隐藏域)
 */
export function getCsrfToken() {
  return (
    readCookie(CSRF_COOKIE_NAME) ||
    document.querySelector('input[name="csrf_token"], input[name="csrftoken"]')
      ?.value ||
    ""
  );
}

let installed = false;

/**
 * 安装全局 fetch 拦截器。幂等,重复调用安全。
 * 必须在应用启动时尽早调用(在任何 fetch 之前)。
 */
export function setupCsrf() {
  if (installed || typeof window === "undefined") return;
  installed = true;

  const originalFetch = window.fetch;
  window.fetch = function csrfFetch(input, init = {}) {
    const method = (init.method || "GET").toUpperCase();

    // 安全方法不需要 CSRF
    if (SAFE_METHODS.has(method)) {
      return originalFetch.call(this, input, init);
    }

    // 已显式设置 header,不覆盖
    const headers = new Headers(init.headers || {});
    if (!headers.has(CSRF_HEADER_NAME)) {
      const token = getCsrfToken();
      if (token) headers.set(CSRF_HEADER_NAME, token);
    }

    return originalFetch.call(this, input, { ...init, headers });
  };
}
