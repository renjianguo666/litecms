import {
  createResource,
  createEffect,
  createMemo,
  createRoot,
  type Resource,
} from "solid-js";
import { useNavigate, useLocation } from "@solidjs/router";
import { auth } from "./api";
import type { UserSchema } from "@/openapi/types.gen";

async function fetchCurrentUser(): Promise<UserSchema | null> {
  try {
    return await auth.me();
  } catch {
    return null;
  }
}

// 使用 createRoot 包裹模块级响应式状态，避免 SolidJS 警告
const authState = createRoot(() => {
  const [user, { mutate, refetch }] = createResource(fetchCurrentUser);
  const permissionSet = createMemo(() => new Set(user()?.permissions ?? []));
  return { user, mutate, refetch, permissionSet };
});

const { user, mutate, refetch, permissionSet } = authState;

// ==========================================
// 权限检查函数
// ==========================================

/**
 * 是否超级用户
 */
export function isSuperuser(): boolean {
  return user()?.is_superuser ?? false;
}

/**
 * 检查单个权限
 */
export function hasPermission(permission: string): boolean {
  // 超级用户拥有所有权限
  if (isSuperuser()) return true;

  const perms = permissionSet();
  // 支持通配符
  if (perms.has("*")) return true;

  return perms.has(permission);
}

/**
 * 检查任意一个权限（满足其一即可）
 */
export function hasAnyPermission(permissions: string[]): boolean {
  if (isSuperuser()) return true;
  return permissions.some((p) => permissionSet().has(p));
}

/**
 * 检查所有权限（必须全部满足）
 */
export function hasAllPermissions(permissions: string[]): boolean {
  if (isSuperuser()) return true;
  return permissions.every((p) => permissionSet().has(p));
}

// ==========================================
// 认证守卫
// ==========================================

export function useAuthGuard(options?: {
  redirectTo?: string;
  persistReturnTo?: boolean;
}) {
  const navigate = useNavigate();
  const location = useLocation();

  createEffect(() => {
    if (user.state === "ready" && !user()) {
      const redirectTo = options?.redirectTo ?? "/login";
      const persist = options?.persistReturnTo ?? true;

      const target = persist
        ? `${redirectTo}?returnTo=${encodeURIComponent(
          location.pathname + location.search,
        )}`
        : redirectTo;

      navigate(target, { replace: true });
    }
  });

  return user;
}

// ==========================================
// 辅助函数
// ==========================================

/**
 * 设置当前用户（登录后）
 */
export function setCurrentUser(nextUser: UserSchema) {
  mutate(() => nextUser);
}

/**
 * 登出
 */
export async function logout() {
  try {
    await auth.logout();
  } finally {
    mutate(() => null);
  }
}

/**
 * 刷新用户信息
 */
export function refreshUser() {
  return refetch();
}

export { user };
export type { Resource };

