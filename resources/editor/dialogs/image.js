import { validateImageUrl } from "../utils/security.js";
import { uploadFile } from "../utils/upload.js";

const BODY_HTML = `
  <div class="form-control mb-3">
    <label class="label label-text font-medium pb-1" for="image-file"><span>本地上传</span></label>
    <div class="drop-zone border-2 border-dashed border-base-300 rounded-box p-4 text-center cursor-pointer hover:border-primary transition-colors"
      data-ref="dropZone">
      <p class="text-sm text-base-content/60 mb-1">点击选择或拖拽图片到此处</p>
      <p class="text-xs text-base-content/40">支持 JPG / PNG / WebP 等常用图片格式</p>
      <input id="image-file" name="image-file" type="file" class="hidden"
        data-ref="file" accept="image/*">
    </div>
    <div class="text-sm text-primary hidden mt-2" data-ref="uploading">上传中...</div>
  </div>
  <div class="divider text-xs text-base-content/50">或</div>
  <div class="form-control mb-3">
    <label class="label label-text font-medium pb-1" for="image-url"><span>图片地址</span></label>
    <input id="image-url" name="image-url" type="url" class="input input-bordered w-full"
      data-ref="url" placeholder="https://example.com/image.jpg">
  </div>
  <div class="form-control mb-3">
    <label class="label label-text font-medium pb-1" for="image-alt"><span>替代文本</span></label>
    <input id="image-alt" name="image-alt" type="text" class="input input-bordered w-full"
      data-ref="alt" placeholder="图片描述(可选)">
  </div>`;

export function getImageDialogConfig(editor, uploadUrl) {
  function updateState(refs, confirmBtn) {
    confirmBtn.disabled = !refs.file.files[0] && !refs.url.value.trim();
  }

  async function handleFileUpload(refs, ctx, file) {
    const { close, confirmBtn } = ctx;
    if (!file.type.startsWith("image/")) {
      alert("请选择图片文件");
      return;
    }

    confirmBtn.disabled = true;
    refs.uploading.classList.remove("hidden");
    refs.uploading.textContent = "上传中...";
    try {
      const url = await uploadFile(file, uploadUrl);
      const alt = refs.alt.value.trim();
      editor.chain().focus().setImage({ src: url, alt: alt || file.name }).run();
      close();
    } catch (e) {
      alert("上传失败:" + e.message);
    } finally {
      refs.uploading.classList.add("hidden");
      updateState(refs, confirmBtn);
    }
  }

  return {
    title: "插入图片",
    bodyHtml: BODY_HTML,
    onOpen(refs, ctx) {
      const { confirmBtn } = ctx;

      refs.dropZone.addEventListener("click", () => refs.file.click());

      ["dragenter", "dragover"].forEach((evt) => {
        refs.dropZone.addEventListener(evt, (e) => {
          e.preventDefault();
          refs.dropZone.classList.add("border-primary", "bg-base-200");
        });
      });
      ["dragleave", "drop"].forEach((evt) => {
        refs.dropZone.addEventListener(evt, (e) => {
          e.preventDefault();
          refs.dropZone.classList.remove("border-primary", "bg-base-200");
        });
      });
      refs.dropZone.addEventListener("drop", (e) => {
        const files = e.dataTransfer?.files;
        if (files && files[0]) {
          refs.file.files = files;
          updateState(refs, confirmBtn);
          handleFileUpload(refs, ctx, files[0]);
        }
      });

      refs.file.addEventListener("change", () => {
        updateState(refs, confirmBtn);
        if (refs.file.files[0]) handleFileUpload(refs, ctx, refs.file.files[0]);
      });

      refs.url.addEventListener("input", () => updateState(refs, confirmBtn));
      updateState(refs, confirmBtn);
    },
    async onConfirm(refs, ctx) {
      if (refs.file.files[0]) {
        await handleFileUpload(refs, ctx, refs.file.files[0]);
        return;
      }

      const url = refs.url.value.trim();
      const alt = refs.alt.value.trim();
      const safe = validateImageUrl(url);
      if (!safe) {
        alert("图片地址格式无效");
        return;
      }
      editor.chain().focus().setImage({ src: safe, alt }).run();
      ctx.close();
    },
  };
}
