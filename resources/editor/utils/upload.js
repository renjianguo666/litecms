/**
 * 图片上传共享工具
 *
 * 后端约定:
 *   file 字段 -> 文件上传
 *   url  字段 -> 外链转存
 *   响应 {"url": "..."} 成功 / {"error": "..."} 失败
 */

export async function uploadFile(file, uploadUrl) {
  const fd = new FormData();
  fd.append("file", file);
  return request(fd, uploadUrl);
}

export async function uploadRemote(url, uploadUrl) {
  const fd = new FormData();
  fd.append("url", url);
  return request(fd, uploadUrl);
}

async function request(fd, uploadUrl) {
  if (!uploadUrl) throw new Error("未配置上传接口");
  const res = await fetch(uploadUrl, { method: "POST", body: fd });
  const data = await res.json().catch(() => ({}));
  if (!res.ok || data.error) {
    throw new Error(data.error || data.detail || `HTTP ${res.status}`);
  }
  if (!data.url) throw new Error("未返回 URL");
  return data.url;
}
