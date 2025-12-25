import { Search } from "lucide-solid";
import { ToolbarButton, ToolbarGroup } from "./button";

/**
 * 搜索组属性
 */
export interface SearchGroupProps {
  /** 点击搜索按钮 */
  onSearchClick: () => void;
}

/**
 * 搜索按钮组
 *
 * 提供查找替换功能入口按钮。
 */
export function SearchGroup(props: SearchGroupProps) {
  return (
    <ToolbarGroup>
      <ToolbarButton onClick={props.onSearchClick} title="查找替换 (Ctrl+F)">
        <Search class="w-4 h-4" />
      </ToolbarButton>
    </ToolbarGroup>
  );
}

export default SearchGroup;
