/**
 * 共享模态对话框 -- 所有弹窗复用同一个 <dialog> 元素
 * 每次打开时切换标题和 body 内容,重新查询 data-ref 引用
 *
 * API:
 *   const modal = createSharedModal();
 *   modal.el    -- <dialog> 元素
 *   modal.open(config)  -- 打开对话框
 *   modal.close()       -- 关闭对话框
 *
 *   config = {
 *     title: string,
 *     bodyHtml: string,
 *     wide: boolean,
 *     onOpen(refs, ctx)   -- 打开时回调,用于填充表单和绑定事件
 *     onConfirm(refs, ctx)  -- 点击确定时回调
 *   }
 *   refs = { [key: string]: HTMLElement }  -- body 中带 data-ref 的元素
 *   ctx = { close, confirmBtn }  -- 关闭函数和确定按钮引用
 */
export function createSharedModal() {
  const dialogEl = document.createElement("dialog");
  dialogEl.className = "modal";
  dialogEl.innerHTML = `
    <div class="modal-box">
      <h3 class="text-lg font-bold pb-2"></h3>
      <div class="py-4"></div>
      <div class="modal-action">
        <button type="button" class="btn btn-soft" data-action="cancel">取消</button>
        <button type="button" class="btn btn-neutral" data-action="confirm">确定</button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop"><button type="submit">close</button></form>
  `;

  const titleEl = dialogEl.querySelector("h3");
  const bodyEl = dialogEl.querySelector(".py-4");
  const modalBox = dialogEl.querySelector(".modal-box");
  const confirmBtn = dialogEl.querySelector('[data-action="confirm"]');
  const cancelBtn = dialogEl.querySelector('[data-action="cancel"]');

  let current = null;
  const ctx = { close, confirmBtn };

  function close() {
    dialogEl.close();
  }

  function open(config) {
    current = config;
    titleEl.textContent = config.title;
    bodyEl.innerHTML = config.bodyHtml;
    modalBox.classList.toggle("max-w-3xl", !!config.wide);

    // 从新 body 中收集 data-ref 引用
    const refs = {};
    bodyEl.querySelectorAll("[data-ref]").forEach((node) => {
      refs[node.dataset.ref] = node;
    });
    current._refs = refs;

    if (config.onOpen) config.onOpen(refs, ctx);
    requestAnimationFrame(() => dialogEl.showModal());
  }

  confirmBtn.addEventListener("click", () => {
    if (current && current.onConfirm) {
      current.onConfirm(current._refs, ctx);
    }
  });

  cancelBtn.addEventListener("click", close);

  return { el: dialogEl, open, close };
}
