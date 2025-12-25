import { createSignal, createMemo, For, Show, splitProps } from "solid-js";
import { ChevronRight, ChevronDown, Folder, FolderOpen } from "lucide-solid";
import { cn } from "@/lib/utils";

// ============================================================================
// Types
// ============================================================================

export interface TreeNode {
  id: string;
  name: string;
  parent_id: string | null;
  depth: number;
  has_children?: boolean;
}

export interface TreeListProps {
  /** 树形数据（扁平结构，按 depth 排序） */
  nodes: TreeNode[];
  /** 当前选中的值 */
  value: string | null;
  /** 值变化回调 */
  onChange: (id: string | null) => void;
  /** 自定义样式类 */
  class?: string;
  /** 标题 */
  title?: string;
  /** 占位提示 */
  placeholder?: string;
  /** 禁用的节点ID（编辑时禁用自己，不可选但可见） */
  disabledId?: string;
  /** 是否允许选择"无"（顶级） */
  allowEmpty?: boolean;
  /** 空选项文本 */
  emptyLabel?: string;
  /** 是否显示图标 */
  showIcon?: boolean;
}

// ============================================================================
// Constants
// ============================================================================

const LINE_WIDTH = 18;

// ============================================================================
// Hook: useTreeLogic
// ============================================================================

function useTreeLogic(
  nodes: () => TreeNode[],
  disabledId?: () => string | undefined,
) {
  const disabledIdValue = () => disabledId?.();

  // 处理节点，重新计算 has_children
  const processedNodes = createMemo(() => {
    const items = nodes();
    return items.map((node, index) => {
      const nextNode = items[index + 1];
      const hasChildren = nextNode ? nextNode.depth > node.depth : false;
      return {
        ...node,
        has_children: hasChildren,
      };
    });
  });

  // 获取所有可展开节点的 ID
  const getExpandableIds = () =>
    new Set(
      processedNodes()
        .filter((n) => n.has_children)
        .map((n) => n.id),
    );

  const [expanded, setExpanded] = createSignal<Set<string>>(getExpandableIds());
  const [allExpanded, setAllExpanded] = createSignal(true);

  // 切换全部展开/收起
  const toggleAll = () => {
    if (allExpanded()) {
      setExpanded(new Set<string>());
      setAllExpanded(false);
    } else {
      setExpanded(getExpandableIds());
      setAllExpanded(true);
    }
  };

  // 切换单个节点展开/收起
  const toggleExpand = (id: string, e: MouseEvent) => {
    e.stopPropagation();
    const next = new Set(expanded());
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setExpanded(next);
  };

  // 判断节点是否可见
  const isVisible = (index: number): boolean => {
    const nodesList = processedNodes();
    const node = nodesList[index];
    if (node.depth === 0) return true;

    let targetDepth = node.depth - 1;
    for (let i = index - 1; i >= 0 && targetDepth >= 0; i--) {
      const prev = nodesList[i];
      if (prev.depth === targetDepth) {
        if (!expanded().has(prev.id)) {
          return false;
        }
        targetDepth--;
      }
    }
    return true;
  };

  // 判断节点是否是当前层级的最后一个
  const isLastInLevel = (index: number, depth: number): boolean => {
    const nodesList = processedNodes();
    for (let i = index + 1; i < nodesList.length; i++) {
      if (nodesList[i].depth === depth) return false;
      if (nodesList[i].depth < depth) return true;
    }
    return true;
  };

  // 获取树形连接线
  const getTreeLines = (index: number): boolean[] => {
    const nodesList = processedNodes();
    const node = nodesList[index];
    const lines: boolean[] = [];

    for (let d = 0; d < node.depth; d++) {
      let ancestorIdx = -1;
      for (let i = index - 1; i >= 0; i--) {
        if (nodesList[i].depth === d) {
          ancestorIdx = i;
          break;
        }
      }

      if (ancestorIdx === -1) {
        lines.push(false);
        continue;
      }

      lines.push(!isLastInLevel(ancestorIdx, d));
    }

    return lines;
  };

  // 判断节点是否禁用
  const isDisabled = (id: string): boolean => {
    return id === disabledIdValue();
  };

  return {
    processedNodes,
    expanded,
    allExpanded,
    toggleAll,
    toggleExpand,
    isVisible,
    isLastInLevel,
    getTreeLines,
    isDisabled,
  };
}

// ============================================================================
// Component: TreeList
// ============================================================================

function TreeList(props: TreeListProps) {
  const [local] = splitProps(props, [
    "nodes",
    "value",
    "onChange",
    "class",
    "title",
    "placeholder",
    "disabledId",
    "allowEmpty",
    "emptyLabel",
    "showIcon",
  ]);

  const {
    processedNodes,
    expanded,
    allExpanded,
    toggleAll,
    toggleExpand,
    isVisible,
    isLastInLevel,
    getTreeLines,
    isDisabled,
  } = useTreeLogic(
    () => local.nodes,
    () => local.disabledId,
  );

  const selectNode = (id: string | null) => {
    local.onChange(id);
  };

  const selectedName = createMemo(() => {
    if (local.value === null || local.value === "") {
      return local.emptyLabel ?? "无";
    }
    const node = local.nodes.find((n) => n.id === local.value);
    return node?.name ?? "";
  });

  return (
    <div
      data-slot="tree-list"
      class={cn(
        "flex flex-col rounded-lg border bg-card text-card-foreground overflow-hidden",
        local.class,
      )}
    >
      {/* Header */}
      <div class="px-3 py-2 border-b bg-muted/50 shrink-0">
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium">{local.title ?? "选择节点"}</span>
          <button
            type="button"
            class={cn(
              "inline-flex items-center gap-1 px-1.5 py-0.5 text-xs rounded",
              "text-muted-foreground",
              "hover:bg-accent hover:text-accent-foreground",
              "transition-colors",
            )}
            onClick={toggleAll}
          >
            {allExpanded() ? "收起" : "展开"}全部
          </button>
        </div>
        <Show when={local.value !== undefined}>
          <div class="mt-1 text-xs text-muted-foreground">
            已选: <span class="text-primary font-medium">{selectedName()}</span>
          </div>
        </Show>
      </div>

      {/* Tree List */}
      <div class="flex-1 overflow-y-auto py-1 min-h-0">
        {/* Empty Option */}
        <Show when={local.allowEmpty !== false}>
          <div
            class={cn(
              "flex items-center h-7 px-2 mx-1 cursor-pointer select-none rounded-sm",
              "transition-colors duration-150",
              local.value === null || local.value === ""
                ? "bg-primary text-primary-foreground"
                : "hover:bg-accent hover:text-accent-foreground",
            )}
            onClick={() => selectNode(null)}
          >
            <span class="text-sm">{local.emptyLabel ?? "作为顶级"}</span>
          </div>
        </Show>

        <Show
          when={processedNodes().length > 0}
          fallback={
            <div class="py-8 text-center text-sm text-muted-foreground">
              {local.placeholder ?? "暂无数据"}
            </div>
          }
        >
          <For each={processedNodes()}>
            {(node, index) => {
              const disabled = () => isDisabled(node.id);
              const isSelected = () => local.value === node.id;
              const isLast = () => isLastInLevel(index(), node.depth);
              const treeLines = () => getTreeLines(index());
              const isExpanded = () => expanded().has(node.id);

              const lineStyle = () =>
                isSelected()
                  ? "1px solid hsl(var(--primary-foreground) / 0.6)"
                  : "1px solid hsl(var(--muted-foreground) / 0.3)";

              return (
                <Show when={isVisible(index())}>
                  <div
                    class={cn(
                      "group flex items-center h-7 mx-1 select-none rounded-sm",
                      "transition-colors duration-150",
                      disabled() && "opacity-50 cursor-not-allowed",
                      !disabled() &&
                        isSelected() &&
                        "bg-primary text-primary-foreground cursor-pointer",
                      !disabled() &&
                        !isSelected() &&
                        "hover:bg-accent hover:text-accent-foreground cursor-pointer",
                    )}
                    onClick={() => !disabled() && selectNode(node.id)}
                  >
                    {/* Tree Lines */}
                    <div class="flex h-full shrink-0">
                      <For each={treeLines()}>
                        {(showLine) => (
                          <div
                            class="relative h-full"
                            style={{ width: `${LINE_WIDTH}px` }}
                          >
                            <Show when={showLine}>
                              <div
                                class="absolute top-0 h-full"
                                style={{
                                  left: `${LINE_WIDTH / 2}px`,
                                  "border-left": lineStyle(),
                                }}
                              />
                            </Show>
                          </div>
                        )}
                      </For>

                      <div
                        class="relative h-full"
                        style={{ width: `${LINE_WIDTH}px` }}
                      >
                        <div
                          class="absolute top-0"
                          style={{
                            left: `${LINE_WIDTH / 2}px`,
                            height: isLast() ? "50%" : "100%",
                            "border-left": lineStyle(),
                          }}
                        />
                        <div
                          class="absolute"
                          style={{
                            left: `${LINE_WIDTH / 2}px`,
                            top: "50%",
                            width: `${LINE_WIDTH / 2}px`,
                            "border-top": lineStyle(),
                          }}
                        />
                      </div>
                    </div>

                    {/* Expand/Collapse Icon */}
                    <Show
                      when={node.has_children}
                      fallback={<span class="w-4 shrink-0" />}
                    >
                      <button
                        type="button"
                        class={cn(
                          "w-4 h-4 flex items-center justify-center shrink-0 rounded",
                          "transition-transform duration-200",
                          isSelected()
                            ? "text-primary-foreground/80 hover:text-primary-foreground"
                            : "text-muted-foreground hover:text-foreground",
                        )}
                        onClick={(e) => toggleExpand(node.id, e)}
                      >
                        <Show
                          when={isExpanded()}
                          fallback={<ChevronRight class="size-3.5" />}
                        >
                          <ChevronDown class="size-3.5" />
                        </Show>
                      </button>
                    </Show>

                    {/* Folder Icon */}
                    <Show when={local.showIcon !== false}>
                      <span
                        class={cn(
                          "ml-0.5 shrink-0",
                          isSelected()
                            ? "text-primary-foreground/80"
                            : "text-amber-500 dark:text-amber-400",
                        )}
                      >
                        <Show
                          when={node.has_children && isExpanded()}
                          fallback={<Folder class="size-4" />}
                        >
                          <FolderOpen class="size-4" />
                        </Show>
                      </span>
                    </Show>

                    {/* Node Name */}
                    <span
                      class={cn(
                        "text-sm ml-1.5 truncate pr-2",
                        isSelected() && "font-medium",
                      )}
                    >
                      {node.name}
                    </span>

                    {/* Disabled Label */}
                    <Show when={disabled()}>
                      <span class="text-xs text-muted-foreground/60 mr-2">
                        (当前)
                      </span>
                    </Show>
                  </div>
                </Show>
              );
            }}
          </For>
        </Show>
      </div>
    </div>
  );
}

export { TreeList };
