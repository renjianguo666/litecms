import type { Component, JSX } from "solid-js";
import {
    House,
    FileText,
    FolderOpen,
    Layers,
    Tag,
    Star,
    FileCode,
    Users,
    Shield,
} from "lucide-solid";

/**
 * 路由配置接口
 */
export interface RouteConfig {
    /** 路由路径 */
    path: string;
    /** 页面标题 */
    title: string;
    /** 页面组件（懒加载） */
    component: () => Promise<{ default: Component }>;

    // 菜单相关
    /** 菜单图标 */
    icon?: (props: { class?: string }) => JSX.Element;
    /** 是否显示在侧边栏菜单 */
    showInMenu?: boolean;
    /** 菜单排序（数字越小越靠前） */
    menuOrder?: number;

    // 权限相关（字符串与后端 PermissionGuard 一致）
    /** 访问此路由所需权限 */
    permission?: string;

    /** 子路由 */
    children?: Omit<RouteConfig, "icon" | "showInMenu" | "menuOrder">[];
}

/**
 * 统一路由配置
 * - 权限字符串与后端 PermissionGuard 保持一致
 * - 菜单从此配置动态生成
 */
export const routesConfig: RouteConfig[] = [
    // ==========================================
    // 仪表盘
    // ==========================================
    {
        path: "/",
        title: "仪表盘",
        component: () => import("@/pages"),
        icon: House,
        showInMenu: true,
        menuOrder: 0,
        // 无 permission = 登录即可访问
    },

    // ==========================================
    // 内容管理
    // ==========================================
    {
        path: "/articles",
        title: "文章管理",
        component: () => import("@/pages/articles"),
        icon: FileText,
        showInMenu: true,
        menuOrder: 1,
        permission: "articles:view_article",
        children: [
            {
                path: "/articles/create",
                title: "新建文章",
                component: () => import("@/pages/articles/create"),
                permission: "articles:create_article",
            },
            {
                path: "/articles/:id",
                title: "编辑文章",
                component: () => import("@/pages/articles/edit"),
                permission: "articles:update_article",
            },
        ],
    },
    {
        path: "/categories",
        title: "栏目管理",
        component: () => import("@/pages/categories"),
        icon: FolderOpen,
        showInMenu: true,
        menuOrder: 2,
        permission: "taxonomies:view_category",
        children: [
            {
                path: "/categories/create",
                title: "新建栏目",
                component: () => import("@/pages/categories/create"),
                permission: "taxonomies:create_category",
            },
            {
                path: "/categories/:id",
                title: "编辑栏目",
                component: () => import("@/pages/categories/edit"),
                permission: "taxonomies:update_category",
            },
        ],
    },
    {
        path: "/specials",
        title: "专题管理",
        component: () => import("@/pages/specials"),
        icon: Layers,
        showInMenu: true,
        menuOrder: 3,
        permission: "taxonomies:view_special",
        children: [
            {
                path: "/specials/create",
                title: "新建专题",
                component: () => import("@/pages/specials/create"),
                permission: "taxonomies:create_special",
            },
            {
                path: "/specials/:id",
                title: "编辑专题",
                component: () => import("@/pages/specials/edit"),
                permission: "taxonomies:update_special",
            },
            {
                path: "/specials/:id/contents",
                title: "专题内容管理",
                component: () => import("@/pages/specials/contents"),
                permission: "taxonomies:view_special_content",
            },
        ],
    },
    {
        path: "/tags",
        title: "标签管理",
        component: () => import("@/pages/tags"),
        icon: Tag,
        showInMenu: true,
        menuOrder: 4,
        permission: "taxonomies:view_tag",
        children: [
            {
                path: "/tags/create",
                title: "新建标签",
                component: () => import("@/pages/tags/create"),
                permission: "taxonomies:create_tag",
            },
            {
                path: "/tags/:id",
                title: "编辑标签",
                component: () => import("@/pages/tags/edit"),
                permission: "taxonomies:update_tag",
            },
            {
                path: "/tags/:id/contents",
                title: "标签内容管理",
                component: () => import("@/pages/tags/contents"),
                permission: "taxonomies:view_tag_content",
            },
        ],
    },
    {
        path: "/features",
        title: "推荐管理",
        component: () => import("@/pages/features"),
        icon: Star,
        showInMenu: true,
        menuOrder: 5,
        permission: "taxonomies:view_feature",
        children: [
            {
                path: "/features/create",
                title: "新建推荐位",
                component: () => import("@/pages/features/create"),
                permission: "taxonomies:create_feature",
            },
            {
                path: "/features/:id",
                title: "编辑推荐位",
                component: () => import("@/pages/features/edit"),
                permission: "taxonomies:update_feature",
            },
            {
                path: "/features/:id/contents",
                title: "推荐位内容管理",
                component: () => import("@/pages/features/contents"),
                permission: "taxonomies:view_feature_content",
            },
        ],
    },

    // ==========================================
    // 系统管理
    // ==========================================
    {
        path: "/templates",
        title: "模板管理",
        component: () => import("@/pages/templates"),
        icon: FileCode,
        showInMenu: true,
        menuOrder: 6,
        permission: "themes:view_template",
        children: [
            {
                path: "/templates/*path",
                title: "编辑模板",
                component: () => import("@/pages/templates"),
                permission: "themes:edit_template",
            },
        ],
    },
    {
        path: "/users",
        title: "用户管理",
        component: () => import("@/pages/users"),
        icon: Users,
        showInMenu: true,
        menuOrder: 7,
        permission: "accounts:view_user",
        children: [
            {
                path: "/users/create",
                title: "新建用户",
                component: () => import("@/pages/users/create"),
                permission: "accounts:create_user",
            },
            {
                path: "/users/:id",
                title: "编辑用户",
                component: () => import("@/pages/users/edit"),
                permission: "accounts:update_user",
            },
        ],
    },
    {
        path: "/roles",
        title: "角色管理",
        component: () => import("@/pages/roles"),
        icon: Shield,
        showInMenu: true,
        menuOrder: 8,
        permission: "accounts:view_role",
        children: [
            {
                path: "/roles/create",
                title: "新建角色",
                component: () => import("@/pages/roles/create"),
                permission: "accounts:create_role",
            },
            {
                path: "/roles/:id",
                title: "编辑角色",
                component: () => import("@/pages/roles/edit"),
                permission: "accounts:update_role",
            },
        ],
    },

    // ==========================================
    // 账号相关（不在菜单显示）
    // ==========================================
    {
        path: "/account/password",
        title: "修改密码",
        component: () => import("@/pages/account/password"),
        showInMenu: false,
    },
];

/**
 * 计算路由优先级分数（分数越高越先匹配）
 * - 路径段越多，优先级越高
 * - 静态段比动态段(:param)优先级高
 * - 包含固定子路径（如 /entries）比纯动态路径优先级高
 */
function getRouteScore(path: string): number {
    const segments = path.split("/").filter(Boolean);
    let score = segments.length * 10; // 基础分：路径段数量

    for (const segment of segments) {
        if (segment.startsWith(":")) {
            // 动态段扣分
            score -= 1;
        } else {
            // 静态段加分
            score += 5;
        }
    }

    return score;
}

/**
 * 获取所有路由（展平，包含子路由）
 * 按优先级排序：更具体的路由先匹配
 */
export function getFlatRoutes(): Omit<RouteConfig, "children">[] {
    const result: Omit<RouteConfig, "children">[] = [];

    for (const route of routesConfig) {
        const { children, ...routeWithoutChildren } = route;
        result.push(routeWithoutChildren);

        if (children) {
            for (const child of children) {
                result.push(child);
            }
        }
    }

    // 按分数降序排列（高分优先匹配）
    result.sort((a, b) => getRouteScore(b.path) - getRouteScore(a.path));

    return result;
}
