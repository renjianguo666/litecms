/**
 * Vanilla Calendar Pro 日期时间选择器初始化
 * - popover 属性 + 原生 popovertarget：toggle / 外部点击关闭 / Esc 关闭
 * - CSS Anchor Positioning：定位 + 自动翻转（position-try-fallbacks），零 JS
 * - VC：只做内联日历渲染，不碰 inputMode / 内部状态
 *
 * 触发器用 <button popovertarget>（原生 toggle，零 JS）。
 * 显示用 button.textContent，表单值存 hidden input。
 * 选日期/调时间实时同步不关闭（有 time 模式），
 * 关闭靠 popover 原生 light-dismiss + Esc + 再点 button toggle。
 */
import { Calendar } from "vanilla-calendar-pro";

export function initVcDateTimePickers() {
  document.querySelectorAll("[data-vc-inline]").forEach((calEl) => {
    if (calEl.__vcInit) return;
    calEl.__vcInit = true;

    const targetId = calEl.dataset.vcTarget;
    const input = targetId ? document.getElementById(targetId) : null;       // hidden input
    const display = targetId ? document.getElementById(`${targetId}_display`) : null; // 显示按钮
    const popover = calEl.closest("[popover]");
    if (!input || !popover) return;

    // 解析 hidden input 现有值，初始化 VC 选中态
    const initialValue = input.value.trim();
    let initialDate = null;
    let initialTime = "00:00";
    if (initialValue) {
      const [datePart, timePart] = initialValue.split(" ");
      initialDate = datePart;
      initialTime = timePart ? timePart.slice(0, 5) : "00:00";
    }

    // 实时同步：写 hidden input（表单提交）+ 更新 button 文本（显示）
    const syncToInput = (self) => {
      const selectedDates = self.context.selectedDates || [];
      const selectedTime = self.context.selectedTime || "00:00";
      if (selectedDates.length > 0) {
        const val = `${selectedDates[0]} ${selectedTime}:00`;
        input.value = val;
        if (display) {
          display.textContent = val;
          display.classList.remove("text-base-content/40");
          display.classList.add("text-base-content");
        }
      }
    };

    const calendar = new Calendar(calEl, {
      type: "default",
      selectionDatesMode: "single",
      selectionTimeMode: 24,
      selectedDates: initialDate ? [initialDate] : [],
      selectedTime: initialTime,
      locale: "zh-CN",
      onClickDate(self) {
        syncToInput(self);
      },
      onChangeTime(self) {
        syncToInput(self);
      },
    });
    calendar.init();
    calEl.__vcCalendar = calendar;
  });
}

// 启动 + HTMX 重新挂载
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initVcDateTimePickers);
} else {
  initVcDateTimePickers();
}

document.body.addEventListener("htmx:afterSwap", initVcDateTimePickers);
