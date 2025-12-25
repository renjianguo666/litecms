import { Show, type JSX, type ParentProps } from "solid-js";
import { hasPermission, hasAnyPermission } from "@/lib/auth";

interface RequirePermissionProps extends ParentProps {
    /** 所需权限（来自后端定义） */
    permission: string;
    /** 无权限时显示的内容，默认不显示 */
    fallback?: JSX.Element;
}

/**
 * 权限守卫组件 - 单个权限检查
 *
 * @example
 * ```tsx
 * <RequirePermission permission="articles:create_article">
 *   <Button>新建文章</Button>
 * </RequirePermission>
 * ```
 */
export function RequirePermission(props: RequirePermissionProps) {
    return (
        <Show when={hasPermission(props.permission)} fallback={props.fallback}>
            {props.children}
        </Show>
    );
}

interface RequireAnyPermissionProps extends ParentProps {
    /** 所需权限列表（满足任意一个即可） */
    permissions: string[];
    /** 无权限时显示的内容 */
    fallback?: JSX.Element;
}

/**
 * 权限守卫组件 - 多个权限检查（任一满足）
 *
 * @example
 * ```tsx
 * <RequireAnyPermission permissions={["articles:update_article", "articles:delete_article"]}>
 *   <ActionsMenu />
 * </RequireAnyPermission>
 * ```
 */
export function RequireAnyPermission(props: RequireAnyPermissionProps) {
    return (
        <Show when={hasAnyPermission(props.permissions)} fallback={props.fallback}>
            {props.children}
        </Show>
    );
}
