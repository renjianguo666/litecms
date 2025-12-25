import { Route, Navigate } from "@solidjs/router";
import { lazy, Show, For, type Component } from "solid-js";

// 页面组件（直接导入，不走 routes-config 的懒加载）
import LoginPage from "./pages/auth/login";
import DashboardLayout from "./pages/layout";
import NotFoundPage from "./pages/404";

import { hasPermission } from "@/lib/auth";
import { getFlatRoutes } from "@/lib/routes-config";

/**
 * 创建带权限检查的路由组件
 */
function createProtectedComponent(
  LazyComponent: Component,
  permission?: string
): Component {
  if (!permission) {
    return LazyComponent;
  }

  return function ProtectedRoute() {
    return (
      <Show when={hasPermission(permission)} fallback={<Navigate href="/" />}>
        <LazyComponent />
      </Show>
    );
  };
}

/**
 * 预生成所有路由配置（模块级别，只执行一次）
 */
const flatRoutes = getFlatRoutes();

// 预创建路由配置（包含组件和元信息）
const routeConfigs = flatRoutes.map((route) => {
  const LazyComponent = lazy(route.component);
  return {
    path: route.path,
    title: route.title,
    component: createProtectedComponent(LazyComponent, route.permission),
  };
});

export function AppRoutes() {
  return (
    <>
      {/* 登录页 */}
      <Route path="/login" component={LoginPage} />

      {/* Dashboard 嵌套路由 */}
      <Route path="/" component={DashboardLayout}>
        <For each={routeConfigs}>
          {(route) => (
            <Route
              path={route.path}
              component={route.component}
              info={{ title: route.title }}
            />
          )}
        </For>

        {/* 404 - 放在 Dashboard 内，保持侧边栏 */}
        <Route path="*404" component={NotFoundPage} info={{ title: "页面不存在" }} />
      </Route>
    </>
  );
}

