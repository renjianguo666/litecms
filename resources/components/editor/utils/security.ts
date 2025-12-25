/**
 * 安全工具函数
 * 用于验证和清理用户输入的 URL
 */

/**
 * 允许的媒体域名白名单
 */
export const ALLOWED_DOMAINS = [
  // 视频平台
  "youtube.com",
  "www.youtube.com",
  "youtu.be",
  "vimeo.com",
  "player.vimeo.com",
  "bilibili.com",
  "www.bilibili.com",
  "player.bilibili.com",

  // 图片平台
  "imgur.com",
  "i.imgur.com",
  "unsplash.com",
  "images.unsplash.com",

  // CDN
  "cloudinary.com",
  "res.cloudinary.com",
  "cdn.jsdelivr.net",

  // 本地开发
  "localhost",
  "127.0.0.1",
];

/**
 * 检查 URL 是否在允许的域名列表中
 */
export function isAllowedUrl(url: string): boolean {
  try {
    const urlObj = new URL(url);
    const hostname = urlObj.hostname.toLowerCase();

    return ALLOWED_DOMAINS.some(
      (domain) => hostname === domain || hostname.endsWith(`.${domain}`),
    );
  } catch {
    return false;
  }
}

/**
 * 检查是否为有效的 HTTP/HTTPS URL
 */
export function isValidHttpUrl(url: string): boolean {
  try {
    const urlObj = new URL(url);
    return urlObj.protocol === "http:" || urlObj.protocol === "https:";
  } catch {
    return false;
  }
}

/**
 * 检查是否为有效的相对 URL
 */
export function isValidRelativeUrl(url: string): boolean {
  return url.startsWith("/") && !url.startsWith("//");
}

/**
 * 清理媒体 URL
 * 移除潜在的恶意参数
 */
export function sanitizeMediaUrl(url: string): string {
  if (!url) return "";

  // 如果是相对路径，直接返回
  if (isValidRelativeUrl(url)) {
    return url;
  }

  try {
    const urlObj = new URL(url);

    // 只保留基本的查询参数
    const safeParams = ["v", "t", "start", "end", "autoplay", "loop", "mute"];
    const newParams = new URLSearchParams();

    urlObj.searchParams.forEach((value, key) => {
      if (safeParams.includes(key.toLowerCase())) {
        newParams.set(key, value);
      }
    });

    urlObj.search = newParams.toString();
    return urlObj.toString();
  } catch {
    return "";
  }
}

/**
 * 检查是否为有效的嵌入 URL（YouTube, Vimeo, Bilibili 等）
 */
export function isValidEmbedUrl(url: string): boolean {
  if (!isValidHttpUrl(url)) return false;

  const embedPatterns = [
    /^https?:\/\/(www\.)?youtube\.com\/embed\//,
    /^https?:\/\/(www\.)?youtube-nocookie\.com\/embed\//,
    /^https?:\/\/player\.vimeo\.com\/video\//,
    /^https?:\/\/player\.bilibili\.com\/player\.html/,
  ];

  return embedPatterns.some((pattern) => pattern.test(url));
}

/**
 * 将普通 YouTube URL 转换为嵌入 URL
 */
export function convertToEmbedUrl(url: string): string | null {
  try {
    const urlObj = new URL(url);
    const hostname = urlObj.hostname.toLowerCase();

    // YouTube
    if (hostname.includes("youtube.com") || hostname.includes("youtu.be")) {
      let videoId = "";

      if (hostname.includes("youtu.be")) {
        videoId = urlObj.pathname.slice(1);
      } else {
        videoId = urlObj.searchParams.get("v") || "";
      }

      if (videoId) {
        return `https://www.youtube.com/embed/${videoId}`;
      }
    }

    // Vimeo
    if (hostname.includes("vimeo.com")) {
      const match = urlObj.pathname.match(/\/(\d+)/);
      if (match) {
        return `https://player.vimeo.com/video/${match[1]}`;
      }
    }

    // Bilibili
    if (hostname.includes("bilibili.com")) {
      const match = urlObj.pathname.match(/\/video\/(BV\w+)/);
      if (match) {
        return `https://player.bilibili.com/player.html?bvid=${match[1]}`;
      }
    }

    return null;
  } catch {
    return null;
  }
}

/**
 * 验证并清理 URL，返回安全的 URL 或 null
 * @param url - 要验证的 URL
 * @param checkDomain - 是否检查域名白名单，默认 false
 */
export function validateAndSanitizeUrl(
  url: string,
  checkDomain: boolean = false,
): string | null {
  if (!url) return null;

  // 相对路径直接返回
  if (isValidRelativeUrl(url)) {
    return url;
  }

  // 必须是有效的 HTTP URL
  if (!isValidHttpUrl(url)) {
    return null;
  }

  // 检查域名白名单
  if (checkDomain && !isAllowedUrl(url)) {
    return null;
  }

  return sanitizeMediaUrl(url);
}
