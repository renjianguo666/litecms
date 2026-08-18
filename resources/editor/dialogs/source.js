import { cleanEditorHtml, cleanAttributes } from "../utils/format.js";

const BODY_HTML = `
  <div class="w-full" style="height:50vh">
    <label class="label label-text font-medium pb-1" for="editor-source-html"><span>HTML 源代码</span></label>
    <textarea id="editor-source-html" name="editor-source-html"
      class="textarea textarea-bordered w-full font-mono text-sm leading-relaxed h-full"
      data-ref="html" rows="20" spellcheck="false"></textarea>
  </div>`;

export function getSourceDialogConfig(editor) {
  return {
    title: "HTML 源代码",
    bodyHtml: BODY_HTML,
    wide: true,
    onOpen(refs) {
      refs.html.value = cleanEditorHtml(editor.getHTML());
    },
    onConfirm(refs, { close }) {
      const html = refs.html.value || "<p></p>";
      try {
        editor.chain().focus().setContent(cleanAttributes(html)).run();
        close();
      } catch (e) {
        alert("HTML 解析失败:" + e.message);
      }
    },
  };
}
