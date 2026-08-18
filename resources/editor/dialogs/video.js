import {
  validateVideoUrl,
  convertToEmbedUrl,
  isValidEmbedUrl,
} from "../utils/security.js";

const BODY_HTML = `
  <div class="join mb-3 w-full">
    <button type="button" class="join-item btn btn-sm btn-active flex-1" data-ref="tabEmbed">嵌入视频</button>
    <button type="button" class="join-item btn btn-sm flex-1" data-ref="tabFile">视频文件</button>
  </div>
  <div class="form-control mb-3">
    <label class="label label-text font-medium pb-1" for="video-url"><span>视频链接</span></label>
    <textarea id="video-url" name="video-url"
      class="textarea textarea-bordered w-full font-mono text-sm leading-relaxed"
      data-ref="url" rows="3"
      placeholder="粘贴 Bilibili、腾讯、优酷、西瓜 链接或 iframe 嵌入代码"></textarea>
    <p class="text-xs text-base-content/50 mt-1">支持 Bilibili、腾讯、优酷、西瓜</p>
  </div>`;

export function getVideoDialogConfig(editor) {
  let mode = "embed";

  return {
    title: "插入视频",
    bodyHtml: BODY_HTML,
    onOpen(refs, { close, confirmBtn }) {
      mode = "embed";
      refs.url.value = "";

      function updateState() {
        confirmBtn.disabled = !refs.url.value.trim();
      }

      function switchTab(m) {
        mode = m;
        const isEmbed = m === "embed";
        refs.tabEmbed.classList.toggle("btn-active", isEmbed);
        refs.tabFile.classList.toggle("btn-active", !isEmbed);
        refs.url.placeholder = isEmbed
          ? "粘贴 Bilibili、腾讯、优酷、西瓜 链接或 iframe 嵌入代码"
          : "https://example.com/video.mp4";
        updateState();
      }

      refs.tabEmbed.addEventListener("click", () => switchTab("embed"));
      refs.tabFile.addEventListener("click", () => switchTab("file"));
      refs.url.addEventListener("input", updateState);

      switchTab("embed");
    },
    onConfirm(refs, { close }) {
      const url = refs.url.value.trim();

      if (mode === "embed") {
        let embedUrl = url;
        const srcMatch = url.match(/src=["']([^"']+)["']/);
        if (srcMatch) embedUrl = srcMatch[1];

        if (!isValidEmbedUrl(embedUrl)) {
          const converted = convertToEmbedUrl(embedUrl);
          if (!converted) {
            alert("无法识别的视频链接格式");
            return;
          }
          embedUrl = converted;
        }
        editor.chain().focus().setIframe({ src: embedUrl }).run();
      } else {
        const safe = validateVideoUrl(url);
        if (!safe) {
          alert("视频 URL 格式无效");
          return;
        }
        editor.chain().focus().setVideo({ src: safe }).run();
      }
      close();
    },
  };
}
