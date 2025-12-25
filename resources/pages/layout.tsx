import { Suspense, Show, For, createSignal, createMemo } from "solid-js";
import { A, useNavigate, useCurrentMatches } from "@solidjs/router";
import type { ParentProps } from "solid-js";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { PageSkeleton } from "@/components/ui/skeleton";
import { ErrorBoundary } from "@/components/error-boundary";
import {
  Menu,
  Bell,
  Sun,
  Moon,
  LogOut,
  Loader,
  X,
  ChevronDown,
  KeyRound,
} from "lucide-solid";
import { useAuthGuard, logout, hasPermission } from "@/lib/auth";
import { SidebarProvider, useSidebar } from "@/components/sidebar";
import { routesConfig } from "@/lib/routes-config";

function LoadingScreen() {
  return (
    <div class="flex min-h-screen items-center justify-center bg-muted/40">
      <Loader class="h-8 w-8 animate-spin text-muted-foreground" />
    </div>
  );
}

/**
 * 从路由配置动态生成菜单项，并根据权限过滤
 */
function getMenuItems() {
  return routesConfig
    .filter((route) => route.showInMenu) // 只显示菜单项
    .filter((route) => !route.permission || hasPermission(route.permission)) // 权限过滤
    .sort((a, b) => (a.menuOrder ?? 0) - (b.menuOrder ?? 0)) // 排序
    .map((route) => ({
      name: route.title,
      path: route.path,
      icon: route.icon!,
    }));
}

function ProtectedShellInner(props: ParentProps) {
  const navigate = useNavigate();
  const currentMatches = useCurrentMatches();
  const currentUser = useAuthGuard();

  const { isOpen: sidebarOpen, toggle: toggleSidebar } = useSidebar();
  const [mobileSidebarOpen, setMobileSidebarOpen] = createSignal(false);


  // 主题状态持久化：读取 localStorage 或系统偏好
  const getInitialTheme = () => {
    if (typeof window === "undefined") return false;
    const saved = localStorage.getItem("theme");
    if (saved) return saved === "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  };
  const [isDark, setIsDark] = createSignal(getInitialTheme());

  // 初始化时同步 DOM
  if (typeof document !== "undefined" && isDark()) {
    document.documentElement.classList.add("dark");
  }

  // 动态菜单：根据用户权限过滤
  const menuItems = createMemo(() => getMenuItems());

  const pageTitle = () => {
    const matches = currentMatches();
    if (matches.length > 0) {
      const last = matches[matches.length - 1];
      const info = last.route.info as { title?: string } | undefined;
      if (info?.title) return info.title;
    }
    return "仪表盘";
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const toggleTheme = () => {
    const newIsDark = !isDark();
    setIsDark(newIsDark);
    localStorage.setItem("theme", newIsDark ? "dark" : "light");
    if (newIsDark) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  const toggleMobileSidebar = () => {
    setMobileSidebarOpen(!mobileSidebarOpen());
  };

  return (
    <Show when={currentUser()} fallback={<LoadingScreen />}>
      <div class="flex h-screen overflow-hidden bg-muted/40">
        {/* 移动端遮罩 */}
        <Show when={mobileSidebarOpen()}>
          <div
            class="fixed inset-0 z-40 bg-black/80 lg:hidden"
            onClick={() => setMobileSidebarOpen(false)}
          />
        </Show>

        {/* 侧边栏 */}
        <aside
          class={`fixed inset-y-0 left-0 z-40 flex flex-col border-r bg-background transition-[width] duration-300 ease-in-out ${mobileSidebarOpen() ? "translate-x-0" : "-translate-x-full"
            } lg:translate-x-0 ${sidebarOpen() ? "w-52" : "w-14"}`}
        >
          {/* Logo */}
          <div class="flex h-14 items-center justify-center border-b px-4">
            <Show when={sidebarOpen()}>
              <A href="/" class="text-lg font-semibold">
                LiteCMS
              </A>
            </Show>
            <Show when={!sidebarOpen()}>
              <A href="/" class="text-lg font-semibold">
                L
              </A>
            </Show>
            {/* 移动端关闭按钮 */}
            <Button
              variant="ghost"
              size="icon"
              class="lg:hidden"
              onClick={() => setMobileSidebarOpen(false)}
            >
              <X class="h-4 w-4" />
              <span class="sr-only">关闭</span>
            </Button>
          </div>

          {/* 导航菜单 */}
          <nav class="flex-1 space-y-1 p-3">
            <ul class="space-y-1">
              <For each={menuItems()}>
                {(item) => (
                  <li>
                    <A
                      href={item.path}
                      class={`flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-all hover:bg-accent hover:text-accent-foreground ${!sidebarOpen() ? "justify-center" : "gap-3"
                        }`}
                      activeClass="bg-primary text-primary-foreground"
                      inactiveClass="text-muted-foreground hover:bg-muted hover:text-foreground"
                      end={item.path === "/"}
                      onClick={() => setMobileSidebarOpen(false)}
                    >
                      <item.icon class="h-4 w-4 shrink-0" />
                      <Show when={sidebarOpen()}>
                        <span
                          class={`whitespace-nowrap transition-all duration-300 ${sidebarOpen()
                            ? "opacity-100 translate-x-0"
                            : "opacity-0 -translate-x-2 w-0 overflow-hidden"
                            }`}
                        >
                          {item.name}
                        </span>
                      </Show>
                    </A>
                  </li>
                )}
              </For>
            </ul>
          </nav>

          {/* 侧边栏折叠按钮 (桌面端) */}
          <div class="hidden border-t lg:block">
            <Button
              variant="ghost"
              size="sm"
              class="w-full"
              onClick={toggleSidebar}
            >
              <ChevronDown
                class={`h-4 w-4 transition-transform duration-200 ${sidebarOpen() ? "rotate-90" : "-rotate-90"
                  }`}
              />
              <span class="sr-only">折叠侧边栏</span>
            </Button>
          </div>
        </aside>

        {/* 主内容区 */}
        <div
          class={`flex min-w-0 flex-1 flex-col h-screen overflow-hidden transition-[margin] duration-300 ease-in-out ${sidebarOpen() ? "lg:ml-52" : "lg:ml-14"
            }`}
        >
          {/* 顶部导航栏 */}
          <header class="sticky top-0 z-30 flex h-14 items-center gap-4 border-b bg-background/95 px-4 backdrop-blur supports-backdrop-filter:bg-background/60 sm:px-6">
            {/* 移动端菜单按钮 */}
            <Button
              variant="ghost"
              size="icon"
              class="shrink-0 lg:hidden"
              onClick={toggleMobileSidebar}
            >
              <Menu class="h-5 w-5" />
              <span class="sr-only">打开菜单</span>
            </Button>

            {/* 桌面端折叠按钮 */}
            <Button
              variant="ghost"
              size="icon"
              class="hidden shrink-0 lg:flex"
              onClick={toggleSidebar}
            >
              <Menu class="h-5 w-5" />
              <span class="sr-only">切换侧边栏</span>
            </Button>

            <h1 class="text-lg font-semibold">{pageTitle()}</h1>

            <div class="ml-auto flex items-center gap-1">

              {/* 通知按钮 */}
              <Button variant="ghost" size="icon">
                <Bell class="h-5 w-5" />
                <span class="sr-only">通知</span>
              </Button>

              {/* 主题切换 */}
              <Button variant="ghost" size="icon" onClick={toggleTheme}>
                <Show when={isDark()} fallback={<Moon class="h-5 w-5" />}>
                  <Sun class="h-5 w-5" />
                </Show>
                <span class="sr-only">切换主题</span>
              </Button>

              {/* 用户菜单 */}
              <DropdownMenu>
                <DropdownMenuTrigger class="inline-flex items-center gap-2 rounded-md px-2 py-1.5 text-sm font-medium ring-offset-background transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">
                  <div class="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-sm font-medium text-primary-foreground">
                    {currentUser()?.username?.slice(0, 1).toUpperCase()}
                  </div>
                  <span class="hidden sm:inline">
                    {currentUser()?.username}
                  </span>
                  <ChevronDown class="h-4 w-4 opacity-50" />
                </DropdownMenuTrigger>

                <DropdownMenuContent align="end" class="w-56">
                  <DropdownMenuItem class="gap-2" asChild>
                    <A href="/account/password" class="flex items-center gap-2 w-full">
                      <KeyRound class="h-4 w-4" />
                      <span>修改密码</span>
                    </A>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    class="gap-2 text-destructive focus:bg-destructive/10 focus:text-destructive"
                    onSelect={handleLogout}
                  >
                    <LogOut class="h-4 w-4" />
                    <span>退出登录</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </header>

          {/* 页面内容 */}
          <main class="flex-1 overflow-y-scroll space-y-4 p-6 relative">
            <div class="fixed inset-0 opacity-[0.05] pointer-events-none bg-size-[30px_30px] bg-[linear-gradient(to_right,currentColor_1px,transparent_1px),linear-gradient(to_bottom,currentColor_1px,transparent_1px)] text-foreground -z-10" />
            <ErrorBoundary>
              <Suspense fallback={<PageSkeleton />}>
                {props.children}
              </Suspense>
            </ErrorBoundary>
          </main>
        </div>
      </div>
    </Show>
  );
}

function ProtectedShell(props: ParentProps) {
  return (
    <SidebarProvider>
      <ProtectedShellInner>{props.children}</ProtectedShellInner>
    </SidebarProvider>
  );
}

export default function DashboardLayout(props: ParentProps) {
  return (
    <ProtectedShell>{props.children}</ProtectedShell>
  );
}
