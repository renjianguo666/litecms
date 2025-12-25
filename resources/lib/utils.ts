import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
/**
 * 从 HTML meta 标签读取并规范化 basepath
 * @param metaName - meta 标签的 name 属性，默认 'app-basepath'
 * @param fallback - 回退值，默认 '/admin'
 * @returns 规范化的 basepath（前导 /，无末尾 /）
 */
export function getBasePathFromMeta(
  metaName: string = "app-basepath",
  fallback: string = "/admin",
): string {
  // SSR 安全
  if (typeof document === "undefined") {
    return fallback;
  }

  const meta = document.querySelector(`meta[name="${metaName}"]`);
  const content = meta?.getAttribute("content")?.trim();

  if (!content) {
    return fallback;
  }

  // 规范化：确保前导 /，移除末尾 /（根路径除外）
  let normalized = content.startsWith("/") ? content : "/" + content;
  if (normalized.length > 1 && normalized.endsWith("/")) {
    normalized = normalized.slice(0, -1);
  }

  return normalized;
}

// Encode helpers for URL search params
export function encodeToBinary(value: string): string {
  return btoa(
    encodeURIComponent(JSON.stringify(value)).replace(
      /%([0-9A-F]{2})/g,
      function (_, p1) {
        return String.fromCharCode(parseInt(p1, 16));
      },
    ),
  ).replace(/=+$/, "");
}

// Decode function
export function decodeFromBinary(value: string): string {
  return JSON.parse(
    decodeURIComponent(
      Array.prototype.map
        .call(atob(value), function (c) {
          return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
        })
        .join(""),
    ),
  );
}
