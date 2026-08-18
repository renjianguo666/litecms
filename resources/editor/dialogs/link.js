import { validateLinkUrl } from "../utils/security.js";

const BODY_HTML = `
  <div class="form-control mb-3">
    <label class="label label-text font-medium pb-1" for="link-url"><span>链接地址</span></label>
    <input id="link-url" name="link-url" type="url" class="input input-bordered w-full"
      data-ref="url" placeholder="https://example.com">
  </div>
  <div class="form-control mb-3">
    <label class="label label-text font-medium pb-1" for="link-text"><span>链接文本</span></label>
    <input id="link-text" name="link-text" type="text" class="input input-bordered w-full"
      data-ref="text" placeholder="显示文本(可选)">
  </div>
  <button type="button" class="btn btn-sm btn-error btn-outline w-full mt-2 hidden" data-ref="remove">移除链接</button>`;

export function getLinkDialogConfig(editor) {
  return {
    title: "插入链接",
    bodyHtml: BODY_HTML,
    onOpen(refs, { close, confirmBtn }) {
      const attrs = editor.getAttributes("link");
      refs.url.value = attrs.href || "";
      const { from, to } = editor.state.selection;
      refs.text.value = editor.state.doc.textBetween(from, to, "");
      refs.remove.hidden = !editor.isActive("link");

      function updateState() {
        confirmBtn.disabled = !refs.url.value.trim();
      }

      updateState();

      refs.url.addEventListener("input", updateState);
      refs.remove.addEventListener("click", () => {
        editor.chain().focus().extendMarkRange("link").unsetLink().run();
        close();
      });
    },
    onConfirm(refs, { close }) {
      const url = refs.url.value.trim();
      const text = refs.text.value.trim();
      const safe = validateLinkUrl(url);
      if (!safe) {
        alert("链接地址格式无效");
        return;
      }

      if (text) {
        const { from, to } = editor.state.selection;
        const hasSelection = from !== to;
        if (hasSelection) {
          let hasMedia = false;
          editor.state.doc.nodesBetween(from, to, (node) => {
            if (node.isBlock && !node.isTextblock) hasMedia = true;
          });
          if (hasMedia) {
            alert("选区包含媒体节点,无法替换为文本");
            return;
          }
        }
        editor
          .chain()
          .focus()
          .deleteSelection()
          .insertContent({
            type: "text",
            text,
            marks: [{ type: "link", attrs: { href: safe } }],
          })
          .run();
      } else {
        editor
          .chain()
          .focus()
          .extendMarkRange("link")
          .setLink({ href: safe })
          .run();
      }
      close();
    },
  };
}
