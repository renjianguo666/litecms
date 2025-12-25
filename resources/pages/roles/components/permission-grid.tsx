import { createMemo, For, Show } from "solid-js";
import { Checkbox } from "@/components/ui/checkbox";
import type { PermissionSchema } from "@/openapi/types.gen";

// 模块名称映射
const MODULE_NAMES: Record<string, string> = {
    articles: "文章管理",
    taxonomies: "分类管理",
    accounts: "用户管理",
    settings: "系统设置",
    themes: "模板管理",
    media: "媒体管理",
};

// 操作名称映射
const ACTION_NAMES: Record<string, string> = {
    view: "查看",
    create: "创建",
    update: "编辑",
    delete: "删除",
};

interface PermissionGroup {
    module: string;
    moduleName: string;
    permissions: Array<{
        id: string;
        name: string;
        label: string;
    }>;
}

interface PermissionCheckboxGridProps {
    permissions: PermissionSchema[];
    value: string[];
    onChange: (value: string[]) => void;
}

/**
 * 解析权限名称，提取模块和操作
 */
function parsePermissionName(name: string): { module: string; action: string; target: string } {
    // 格式: module:action_target，如 articles:create_article
    const [module, rest] = name.split(":");
    if (!rest) {
        return { module: "other", action: "", target: name };
    }

    const parts = rest.split("_");
    const action = parts[0];
    const target = parts.slice(1).join("_");

    return { module, action, target };
}

/**
 * 获取权限的友好标签
 */
function getPermissionLabel(permission: PermissionSchema): string {
    if (permission.description) {
        return permission.description;
    }

    const { action, target } = parsePermissionName(permission.name);
    const actionLabel = ACTION_NAMES[action] || action;
    return `${actionLabel}${target}`;
}

/**
 * 按模块分组权限
 */
function groupPermissions(permissions: PermissionSchema[]): PermissionGroup[] {
    const groups: Record<string, PermissionGroup> = {};

    for (const perm of permissions) {
        const { module } = parsePermissionName(perm.name);

        if (!groups[module]) {
            groups[module] = {
                module,
                moduleName: MODULE_NAMES[module] || module,
                permissions: [],
            };
        }

        groups[module].permissions.push({
            id: perm.id,
            name: perm.name,
            label: getPermissionLabel(perm),
        });
    }

    // 按模块名称排序
    return Object.values(groups).sort((a, b) => a.moduleName.localeCompare(b.moduleName));
}

export default function PermissionCheckboxGrid(props: PermissionCheckboxGridProps) {
    const groups = createMemo(() => groupPermissions(props.permissions));
    const selectedSet = createMemo(() => new Set(props.value));

    // 切换单个权限
    const togglePermission = (permId: string) => {
        const current = new Set(props.value);
        if (current.has(permId)) {
            current.delete(permId);
        } else {
            current.add(permId);
        }
        props.onChange(Array.from(current));
    };

    // 切换整个模块
    const toggleModule = (group: PermissionGroup) => {
        const current = new Set(props.value);
        const groupIds = group.permissions.map((p) => p.id);
        const allSelected = groupIds.every((id) => current.has(id));

        if (allSelected) {
            // 取消全选
            groupIds.forEach((id) => current.delete(id));
        } else {
            // 全选
            groupIds.forEach((id) => current.add(id));
        }
        props.onChange(Array.from(current));
    };

    // 检查模块是否全选
    const isModuleAllSelected = (group: PermissionGroup) => {
        return group.permissions.every((p) => selectedSet().has(p.id));
    };

    return (
        <div class="space-y-4">
            <For each={groups()}>
                {(group) => (
                    <div class="rounded-lg border bg-card">
                        {/* 模块标题 */}
                        <div class="flex items-center justify-between border-b px-4 py-3">
                            <div class="flex items-center gap-3">
                                <Checkbox
                                    checked={isModuleAllSelected(group)}
                                    onChange={() => toggleModule(group)}
                                />
                                <span class="font-medium">{group.moduleName}</span>
                                <span class="text-xs text-muted-foreground">
                                    ({group.permissions.filter((p) => selectedSet().has(p.id)).length}/{group.permissions.length})
                                </span>
                            </div>
                        </div>

                        {/* 权限列表 */}
                        <div class="grid grid-cols-2 gap-2 p-4 sm:grid-cols-3 lg:grid-cols-4">
                            <For each={group.permissions}>
                                {(perm) => (
                                    <label class="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors hover:bg-muted">
                                        <Checkbox
                                            checked={selectedSet().has(perm.id)}
                                            onChange={() => togglePermission(perm.id)}
                                        />
                                        <span>{perm.label}</span>
                                    </label>
                                )}
                            </For>
                        </div>
                    </div>
                )}
            </For>

            <Show when={groups().length === 0}>
                <div class="text-center text-sm text-muted-foreground py-8">
                    暂无可用权限
                </div>
            </Show>
        </div>
    );
}
