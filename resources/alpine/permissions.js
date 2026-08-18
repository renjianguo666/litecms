/**
 * 角色权限选择器（分组 checkbox + 组头全选/半选/计数联动）
 * - selected 初始值从参数传入（edit 回显）
 * - groups 分组结构 init 时从 DOM 的 data-group 属性读取
 * - 组内用 x-model="selected" 双向绑定
 * - 用法：x-data="permissionPicker(initialSelected)"
 */
import Alpine from "alpinejs";

Alpine.data("permissionPicker", (initialSelected = []) => ({
  groups: {},
  selected: initialSelected,

  init() {
    this.$el
      .querySelectorAll('input[type="checkbox"][data-group]')
      .forEach((cb) => {
        const key = cb.dataset.group;
        if (!this.groups[key]) this.groups[key] = [];
        this.groups[key].push(cb.value);
      });
  },

  isGroupChecked(groupKey) {
    const ids = this.groups[groupKey] || [];
    return ids.length > 0 && ids.every((id) => this.selected.includes(id));
  },

  isGroupIndeterminate(groupKey) {
    const count = this.checkedCount(groupKey);
    const ids = this.groups[groupKey] || [];
    return count > 0 && count < ids.length;
  },

  checkedCount(groupKey) {
    const ids = this.groups[groupKey] || [];
    return ids.filter((id) => this.selected.includes(id)).length;
  },

  toggleGroup(groupKey, checked) {
    const ids = this.groups[groupKey] || [];
    if (checked) {
      ids.forEach((id) => {
        if (!this.selected.includes(id)) this.selected.push(id);
      });
    } else {
      const idSet = new Set(ids);
      this.selected = this.selected.filter((v) => !idSet.has(v));
    }
  },
}));
