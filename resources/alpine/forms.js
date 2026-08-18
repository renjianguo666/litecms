/**
 * 文章表单相关 Alpine 组件与 store
 * - articleTags store：标签全局状态（modal 与表单共享）
 * - combobox：多选 chips + popover
 * - coverPicker：文章封面选择 + 本地上传
 */
import Alpine from "alpinejs";

// ---------- 文章表单：标签选择（Alpine 全局 store）----------
// Modal 和表单通过 $store.articleTags 共享状态，HTMX 加载的
// 搜索结果也能响应式读取/修改，无需额外 JS 函数。
Alpine.store("articleTags", {
  items: [], // ["标签名", ...] 直接存字符串, 与 form.tags.data 结构一致
  has(name) {
    return this.items.includes(name);
  },
  toggle(name) {
    if (this.has(name)) {
      this.items = this.items.filter((n) => n !== name);
    } else {
      this.items.push(name);
    }
  },
  remove(name) {
    this.items = this.items.filter((n) => n !== name);
  },
});

// ---------- Combobox 组件（多选关联字段，原生 select 增强）----------
// 用法：x-data="combobox"
// 原生 <select multiple> 是真相源（提交用），Alpine 用 selectedValues 镜像状态（响应式）
// 下拉用 popover + CSS Anchor Positioning（和 datetime 宏统一），Alpine 只管状态同步不碰定位
// wasOpen 用于处理 light-dismiss 竞态（见宏注释）
Alpine.data("combobox", () => ({
  selectedValues: [],
  wasOpen: false,

  init() {
    this.select = this.$refs.select;
    this.selectedValues = Array.from(this.select.options)
      .filter((o) => o.selected)
      .map((o) => o.value);
  },

  get options() {
    return Array.from(this.select.options).map((o) => ({
      value: o.value,
      label: o.text,
      selected: this.selectedValues.includes(o.value),
    }));
  },

  get selected() {
    return this.options.filter((o) => o.selected);
  },

  toggle(value) {
    if (this.selectedValues.includes(value)) {
      this.selectedValues = this.selectedValues.filter((v) => v !== value);
    } else {
      this.selectedValues.push(value);
    }
    this.syncToSelect();
  },

  remove(value) {
    this.selectedValues = this.selectedValues.filter((v) => v !== value);
    this.syncToSelect();
  },

  syncToSelect() {
    Array.from(this.select.options).forEach((o) => {
      o.selected = this.selectedValues.includes(o.value);
    });
  },
}));

// ---------- 封面选择器（文章封面选择 + 本地上传）----------
// 用法：<div x-data="coverPicker" data-upload-url="..." data-initial-url="...">
Alpine.data("coverPicker", () => ({
  uploadUrl: "",
  coverUrl: "",
  selectedUrl: "",
  dialogImages: [],
  uploadedImages: [],

  init() {
    this.uploadUrl = this.$el.dataset.uploadUrl || "";
    this.coverUrl = this.$el.dataset.initialUrl || "";
  },

  get hasCover() {
    return !!this.coverUrl.trim();
  },

  getEditorImages() {
    const textarea = document.querySelector("textarea[data-editor]");
    if (!textarea || !textarea.__editor) return [];
    const html = textarea.__editor.getHTML();
    const images = [];
    const re = /<img[^>]+src=["']([^"']+)["']/gi;
    let m;
    while ((m = re.exec(html)) !== null) {
      images.push(m[1]);
    }
    return images;
  },

  openDialog() {
    const editorImages = this.getEditorImages();
    this.dialogImages = [...new Set([...editorImages, ...this.uploadedImages])];
    this.selectedUrl = this.coverUrl.trim() || (this.dialogImages.length ? this.dialogImages[0] : "");
    this.$refs.dialog.showModal();
  },

  closeDialog() {
    this.$refs.dialog.close();
  },

  selectImage(url) {
    this.selectedUrl = url;
  },

  confirmSelection() {
    if (!this.selectedUrl) {
      alert("请选择一张图片");
      return;
    }
    this.coverUrl = this.selectedUrl;
    this.$refs.dialog.close();
  },

  removeCover() {
    this.coverUrl = "";
  },

  async handleUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await fetch(this.uploadUrl, { method: "POST", body: fd });
      const data = await res.json();
      if (data.url) {
        if (!this.uploadedImages.includes(data.url)) {
          this.uploadedImages.push(data.url);
        }
        if (!this.dialogImages.includes(data.url)) {
          this.dialogImages.push(data.url);
        }
        this.selectedUrl = data.url;
      } else {
        alert(data.error || "上传失败");
      }
    } catch (e) {
      alert("上传失败: " + e.message);
    }
    event.target.value = "";
  },
}));
