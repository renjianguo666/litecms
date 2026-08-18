/**
 * 把协议相对 URL(//host/path)补上 https: 前缀
 * B 站、优酷等分享的 embed 代码常用这种格式
 */
function normalizeUrl(url) {
  if (typeof url !== "string") return url;
  const trimmed = url.trim();
  if (trimmed.startsWith("//")) return "https:" + trimmed;
  return trimmed;
}

export function isValidHttpUrl(url) {
  try {
    const urlObj = new URL(normalizeUrl(url));
    return urlObj.protocol === "http:" || urlObj.protocol === "https:";
  } catch {
    return false;
  }
}

export function isValidRelativeUrl(url) {
  return url.startsWith("/") && !url.startsWith("//");
}

/**
 * 清理媒体 URL 的 query 参数(仅保留白名单)
 * 仅用于视频/iframe,不用于图片(图片常带 token 等签名参数)
 */
function sanitizeVideoUrlQuery(url) {
  try {
    const urlObj = new URL(url);
    const safeParams = [
      "v",
      "t",
      "start",
      "end",
      "autoplay",
      "loop",
      "mute",
      "bvid",
      "vid",
      "isOutside",
      "aid",
      "cid",
      "p",
      "page",
    ];
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

export function isValidEmbedUrl(url) {
  const normalized = normalizeUrl(url);
  if (!isValidHttpUrl(normalized)) return false;
  const embedPatterns = [
    /^https?:\/\/(www\.)?youtube\.com\/embed\//,
    /^https?:\/\/(www\.)?youtube-nocookie\.com\/embed\//,
    /^https?:\/\/player\.vimeo\.com\/video\//,
    /^https?:\/\/player\.bilibili\.com\/player\.html/,
    /^https?:\/\/v\.qq\.com\/txp\/iframe\/player\.html/,
    /^https?:\/\/player\.youku\.com\/embed\//,
    /^https?:\/\/player\.ixigua\.com\//,
  ];
  return embedPatterns.some((pattern) => pattern.test(normalized));
}

export function convertToEmbedUrl(url) {
  try {
    const urlObj = new URL(normalizeUrl(url));
    const hostname = urlObj.hostname.toLowerCase();

    // YouTube
    if (hostname.includes("youtube.com") || hostname.includes("youtu.be")) {
      let videoId = "";
      if (hostname.includes("youtu.be")) {
        videoId = urlObj.pathname.slice(1);
      } else {
        videoId = urlObj.searchParams.get("v") || "";
      }
      if (videoId) return `https://www.youtube.com/embed/${videoId}`;
    }

    // Vimeo
    if (hostname.includes("vimeo.com")) {
      const match = urlObj.pathname.match(/\/(\d+)/);
      if (match) return `https://player.vimeo.com/video/${match[1]}`;
    }

    // Bilibili
    if (hostname.includes("bilibili.com")) {
      const match = urlObj.pathname.match(/\/video\/(BV\w+)/);
      if (match)
        return `https://player.bilibili.com/player.html?bvid=${match[1]}`;
    }

    // 腾讯视频 v.qq.com/x/cover/xxx/vid.html
    if (hostname.includes("v.qq.com")) {
      const match = urlObj.pathname.match(/\/([^/]+)\.html$/);
      if (match)
        return `https://v.qq.com/txp/iframe/player.html?vid=${match[1]}`;
    }

    // 优酷 v.youku.com/v_show/id_xxx.html
    if (hostname.includes("youku.com")) {
      const match = urlObj.pathname.match(/id_([A-Za-z0-9=]+)\.html/);
      if (match) return `https://player.youku.com/embed/${match[1]}`;
    }

    // 西瓜视频 ixigua.com
    if (hostname.includes("ixigua.com")) {
      const match = urlObj.pathname.match(/\/(\d+)/);
      if (match) return `https://player.ixigua.com/${match[1]}`;
    }

    return null;
  } catch {
    return null;
  }
}

/**
 * 校验图片 URL —— 原样返回,不删 query(图片常带签名 token)
 */
export function validateImageUrl(url) {
  if (!url) return null;
  if (isValidRelativeUrl(url)) return url;
  if (!isValidHttpUrl(url)) return null;
  return normalizeUrl(url);
}

/**
 * 校验链接 URL —— 不做 query 过滤,链接的所有参数都可能有用
 */
export function validateLinkUrl(url) {
  if (!url) return null;
  if (isValidRelativeUrl(url)) return url;
  if (!isValidHttpUrl(url)) return null;
  return normalizeUrl(url);
}

/**
 * 校验视频文件 URL —— 过滤 query,只保留白名单参数
 */
export function validateVideoUrl(url) {
  if (!url) return null;
  const normalized = normalizeUrl(url);
  if (isValidRelativeUrl(url)) return url;
  if (!isValidHttpUrl(normalized)) return null;
  return sanitizeVideoUrlQuery(normalized);
}
