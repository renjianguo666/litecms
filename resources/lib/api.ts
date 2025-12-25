// 【修正】根据你的配置 resources/openapi，引用路径修正为 @/openapi
import { client } from "@/openapi/client.gen";
// 引入所有生成的 SDK 函数
import * as sdk from "@/openapi/sdk.gen";
// 【新增】引入生成的类型定义 (用于修复 query 类型报错)
import type * as types from "@/openapi/types.gen";
import { z } from "zod";
// 引入生成的 Zod Schemas
import * as zodSchemas from "@/openapi/zod.gen";

// ========================================
// 1. 全局配置 & 拦截器 (替代原来的 Unwrap)
// ========================================

client.setConfig({
  baseUrl: "/",
});

export interface ValidationErrorItem {
  field: string;
  message: string;
}
export interface ApiError {
  status_code: number;
  detail: string;
  extra?: ValidationErrorItem[];
}

/**
 * 统一错误处理辅助函数
 */
const handle = async <T, E>(
  promise: Promise<{ data?: T; error?: E; response: Response }>,
  errorMessage: string = "请求失败",
): Promise<NonNullable<T>> => {
  const { data, error } = await promise;

  if (error) {
    const err = error as unknown as ApiError;
    throw {
      status_code: err?.status_code || 400,
      detail: err?.detail || errorMessage,
      extra: err?.extra,
    } as ApiError;
  }

  return data as NonNullable<T>;
};

// ========================================
// 2. Zod Schema 导出
// ========================================
export {
  userLoginSchema as LoginFormSchema,
  articleCreateSchema as ArticleCreateFormSchema,
  articleUpdateSchema as ArticleUpdateFormSchema,
  categoryCreateSchema as CategoryCreateFormSchema,
  categoryUpdateSchema as CategoryUpdateFormSchema,
  tagCreateSchema as TagCreateFormSchema,
  tagUpdateSchema as TagUpdateFormSchema,
  specialCreateSchema as SpecialCreateFormSchema,
  specialUpdateSchema as SpecialUpdateFormSchema,
  featureCreateSchema as FeatureCreateFormSchema,
  featureUpdateSchema as FeatureUpdateFormSchema,
  userCreateSchema as UserCreateFormSchema,
  userUpdateSchema as UserUpdateFormSchema,
  roleCreateSchema as RoleCreateFormSchema,
  roleUpdateSchema as RoleUpdateFormSchema,
  permissionUpdateSchema as PermissionUpdateFormSchema,
  templateRenameSchema as RenameFormSchema,
} from "@/openapi/zod.gen";

// ========================================
// 3. 业务 API 模块 (适配层)
// ========================================

// Password change form schema with confirm password validation
export const PasswordChangeFormSchema = z
  .object({
    old_password: z.string().min(1, "请输入当前密码"),
    new_password: z.string().min(6, "新密码至少6个字符"),
    confirm_password: z.string().min(1, "请再次输入新密码"),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "两次输入的密码不一致",
    path: ["confirm_password"],
  });

export const auth = {
  async login(body: z.infer<typeof zodSchemas.userLoginSchema>) {
    return handle(sdk.apiLoginLogin({ body }), "登录失败");
  },

  async logout() {
    return handle(sdk.apiLogoutLogout(), "登出失败");
  },

  async me() {
    return handle(sdk.apiMeProfile(), "获取用户信息失败");
  },
};

export const account = {
  async changePassword(body: { old_password: string; new_password: string }) {
    return handle(sdk.apiMePasswordUpdatePassword({ body }), "修改密码失败");
  },
};

export const article = {
  // 【修复】使用 types.ApiArticlesListArticlesData["query"]
  async list(query: types.ApiArticlesListArticlesData["query"] = {}) {
    return handle(sdk.apiArticlesListArticles({ query }), "获取文章列表失败");
  },

  async get(id: string) {
    return handle(
      sdk.apiArticlesItemIdGetArticle({ path: { item_id: id } }),
      "获取文章详情失败",
    );
  },

  async create(body: z.infer<typeof zodSchemas.articleCreateSchema>) {
    return handle(sdk.apiArticlesCreateArticle({ body }), "创建文章失败");
  },

  async update(
    id: string,
    body: z.infer<typeof zodSchemas.articleUpdateSchema>,
  ) {
    return handle(
      sdk.apiArticlesItemIdUpdateArticle({ path: { item_id: id }, body }),
      "更新文章失败",
    );
  },

  async delete(id: string) {
    return handle(
      sdk.apiArticlesItemIdDeleteArticle({ path: { item_id: id } }),
      "删除文章失败",
    );
  },
};

export const category = {
  async list(query: types.ApiCategoriesListCategoriesData["query"] = {}) {
    return handle(
      sdk.apiCategoriesListCategories({ query }),
      "获取分类列表失败",
    );
  },

  async get(id: string) {
    return handle(
      sdk.apiCategoriesItemIdGetCategory({ path: { item_id: id } }),
      "获取分类详情失败",
    );
  },

  async create(body: z.infer<typeof zodSchemas.categoryCreateSchema>) {
    return handle(sdk.apiCategoriesCreateCategory({ body }), "创建分类失败");
  },

  async update(
    id: string,
    body: z.infer<typeof zodSchemas.categoryUpdateSchema>,
  ) {
    return handle(
      sdk.apiCategoriesItemIdUpdateCategory({ path: { item_id: id }, body }),
      "更新分类失败",
    );
  },

  async delete(id: string) {
    return handle(
      sdk.apiCategoriesItemIdDeleteCategory({ path: { item_id: id } }),
      "删除分类失败",
    );
  },
};

export const tag = {
  // 【修复】使用 types.ApiTagsListTagsData["query"]
  async list(query: types.ApiTagsListTagsData["query"] = {}) {
    return handle(sdk.apiTagsListTags({ query }), "获取标签列表失败");
  },

  async get(id: string) {
    return handle(
      sdk.apiTagsItemIdGetTag({ path: { item_id: id } }),
      "获取标签详情失败",
    );
  },

  async create(body: z.infer<typeof zodSchemas.tagCreateSchema>) {
    return handle(sdk.apiTagsCreateTag({ body }), "创建标签失败");
  },

  async update(id: string, body: z.infer<typeof zodSchemas.tagUpdateSchema>) {
    return handle(
      sdk.apiTagsItemIdUpdateTag({ path: { item_id: id }, body }),
      "更新标签失败",
    );
  },

  async delete(id: string) {
    return handle(
      sdk.apiTagsItemIdDeleteTag({ path: { item_id: id } }),
      "删除标签失败",
    );
  },

  async listContents(tagId: string) {
    return handle(
      sdk.apiTagsTagIdContentsListContents({ path: { tag_id: tagId } }),
      "获取标签内容失败",
    );
  },

  async addContents(tagId: string, contentIds: string[]) {
    return handle(
      sdk.apiTagsTagIdContentsPushContents({
        path: { tag_id: tagId },
        body: { content_ids: contentIds },
      }),
      "添加内容到标签失败",
    );
  },

  async removeContent(tagId: string, contentId: string) {
    return handle(
      sdk.apiTagsTagIdContentsContentIdRemoveContent({
        path: { tag_id: tagId, content_id: contentId },
      }),
      "移除标签内容失败",
    );
  },
};

export const special = {
  async list(query: types.ApiSpecialsListSpecialsData["query"] = {}) {
    return handle(sdk.apiSpecialsListSpecials({ query }), "获取专题列表失败");
  },

  async get(id: string) {
    return handle(
      sdk.apiSpecialsSpecialIdGetSpecial({ path: { special_id: id } }),
      "获取专题详情失败",
    );
  },

  async create(body: z.infer<typeof zodSchemas.specialCreateSchema>) {
    return handle(sdk.apiSpecialsCreateSpecial({ body }), "创建专题失败");
  },

  async update(id: string, body: z.infer<typeof zodSchemas.specialUpdateSchema>) {
    return handle(
      sdk.apiSpecialsSpecialIdUpdateSpecial({ path: { special_id: id }, body }),
      "更新专题失败",
    );
  },

  async delete(id: string) {
    return handle(
      sdk.apiSpecialsSpecialIdDeleteSpecial({ path: { special_id: id } }),
      "删除专题失败",
    );
  },

  async listContents(specialId: string) {
    return handle(
      sdk.apiSpecialsSpecialIdContentsListContents({ path: { special_id: specialId } }),
      "获取专题内容失败",
    );
  },

  async addContents(specialId: string, contentIds: string[]) {
    return handle(
      sdk.apiSpecialsSpecialIdContentsPushContents({
        path: { special_id: specialId },
        body: { content_ids: contentIds },
      }),
      "添加内容到专题失败",
    );
  },

  async removeContent(specialId: string, contentId: string) {
    return handle(
      sdk.apiSpecialsSpecialIdContentsContentIdRemoveContent({
        path: { special_id: specialId, content_id: contentId },
      }),
      "移除专题内容失败",
    );
  },

  async sortContents(
    specialId: string,
    items: Array<{ content_id: string; position: number }>,
  ) {
    return handle(
      sdk.apiSpecialsSpecialIdContentsSortSortContents({
        path: { special_id: specialId },
        body: { items },
      }),
      "排序专题内容失败",
    );
  },
};

export const feature = {
  // 【修复】使用 types.ApiFeaturesListFeaturesData["query"]
  async list(query: types.ApiFeaturesListFeaturesData["query"] = {}) {
    return handle(sdk.apiFeaturesListFeatures({ query }), "获取推荐位列表失败");
  },

  async get(id: string) {
    return handle(
      sdk.apiFeaturesItemIdGetFeature({ path: { item_id: id } }),
      "获取推荐位详情失败",
    );
  },

  async create(body: z.infer<typeof zodSchemas.featureCreateSchema>) {
    return handle(sdk.apiFeaturesCreateFeature({ body }), "创建推荐位失败");
  },

  async update(
    id: string,
    body: z.infer<typeof zodSchemas.featureUpdateSchema>,
  ) {
    return handle(
      sdk.apiFeaturesItemIdUpdateFeature({ path: { item_id: id }, body }),
      "更新推荐位失败",
    );
  },

  async delete(id: string) {
    return handle(
      sdk.apiFeaturesItemIdDeleteFeature({ path: { item_id: id } }),
      "删除推荐位失败",
    );
  },

  async listContents(featureId: string) {
    return handle(
      sdk.apiFeaturesFeatureIdContentsListContents({
        path: { feature_id: featureId },
      }),
      "获取推荐位内容失败",
    );
  },

  async addContents(featureId: string, contentIds: string[]) {
    return handle(
      sdk.apiFeaturesFeatureIdContentsPushContents({
        path: { feature_id: featureId },
        body: { content_ids: contentIds },
      }),
      "添加内容到推荐位失败",
    );
  },

  async removeContent(featureId: string, contentId: string) {
    return handle(
      sdk.apiFeaturesFeatureIdContentsContentIdRemoveContent({
        path: { feature_id: featureId, content_id: contentId },
      }),
      "移除推荐位内容失败",
    );
  },
};

export const user = {
  // 【修复】使用 types.ApiUsersListUsersData["query"]
  async list(query: types.ApiUsersListUsersData["query"] = {}) {
    return handle(sdk.apiUsersListUsers({ query }), "获取用户列表失败");
  },

  async get(id: string) {
    return handle(
      sdk.apiUsersItemIdGetUser({ path: { item_id: id } }),
      "获取用户详情失败",
    );
  },

  async create(body: z.infer<typeof zodSchemas.userCreateSchema>) {
    return handle(sdk.apiUsersCreateUser({ body }), "创建用户失败");
  },

  async update(id: string, body: z.infer<typeof zodSchemas.userUpdateSchema>) {
    return handle(
      sdk.apiUsersItemIdUpdateUser({ path: { item_id: id }, body }),
      "更新用户失败",
    );
  },

  async delete(id: string) {
    return handle(
      sdk.apiUsersItemIdDeleteUser({ path: { item_id: id } }),
      "删除用户失败",
    );
  },
};

export const role = {
  // 【修复】使用 types.ApiRolesListRolesData["query"]
  async list(query: types.ApiRolesListRolesData["query"] = {}) {
    return handle(sdk.apiRolesListRoles({ query }), "获取角色列表失败");
  },

  async get(id: string) {
    return handle(
      sdk.apiRolesItemIdGetRole({ path: { item_id: id } }),
      "获取角色详情失败",
    );
  },

  async create(body: z.infer<typeof zodSchemas.roleCreateSchema>) {
    return handle(sdk.apiRolesCreateRole({ body }), "创建角色失败");
  },

  async update(id: string, body: z.infer<typeof zodSchemas.roleUpdateSchema>) {
    return handle(
      sdk.apiRolesItemIdUpdateRole({ path: { item_id: id }, body }),
      "更新角色失败",
    );
  },

  async delete(id: string) {
    return handle(
      sdk.apiRolesItemIdDeleteRole({ path: { item_id: id } }),
      "删除角色失败",
    );
  },
};

export const permission = {
  // 【修复】使用 types.ApiPermissionsListPermissionsData["query"]
  async list(query: types.ApiPermissionsListPermissionsData["query"] = {}) {
    return handle(
      sdk.apiPermissionsListPermissions({ query }),
      "获取权限列表失败",
    );
  },

  async update(
    id: string,
    body: z.infer<typeof zodSchemas.permissionUpdateSchema>,
  ) {
    return handle(
      sdk.apiPermissionsItemIdUpdatePermission({ path: { item_id: id }, body }),
      "更新权限失败",
    );
  },
};

export const template = {
  async list() {
    return handle(sdk.apiTemplatesListTemplates(), "获取模板列表失败");
  },

  async get(path: string) {
    return handle(
      sdk.apiTemplatesFilePathGetTemplate({ path: { file_path: path } }),
      "获取模板内容失败",
    );
  },

  async save(path: string, content: string) {
    return handle(
      sdk.apiTemplatesFilePathSaveTemplate({
        path: { file_path: path },
        body: { content },
      }),
      "保存模板失败",
    );
  },

  async rename(path: string, newName: string) {
    return handle(
      sdk.apiTemplatesFilePathRenameTemplate({
        path: { file_path: path },
        body: { name: newName },
      }),
      "重命名模板失败",
    );
  },

  async delete(path: string) {
    return handle(
      sdk.apiTemplatesFilePathDeleteTemplate({ path: { file_path: path } }),
      "删除模板失败",
    );
  },

  async options() {
    return handle(
      sdk.apiTemplatesOptionsGetTemplateOptions(),
      "获取模板选项失败",
    );
  },
};

export const upload = {
  async upload(file: File, uploadToken: string) {
    return handle(
      sdk.apiUploadUpload({
        query: { upload_token: uploadToken },
        body: { file: file as any },
      }),
      "文件上传失败",
    );
  },
};

// ========================================
// 4. 类型别名导出
// ========================================

// FormValues 类型（对应 Zod Schema 推断类型）
export type ArticleCreateFormValues = z.infer<
  typeof zodSchemas.articleCreateSchema
>;
export type ArticleUpdateFormValues = z.infer<
  typeof zodSchemas.articleUpdateSchema
>;
export type CategoryCreateFormValues = z.infer<
  typeof zodSchemas.categoryCreateSchema
>;
export type CategoryUpdateFormValues = z.infer<
  typeof zodSchemas.categoryUpdateSchema
>;
export type TagCreateFormValues = z.infer<typeof zodSchemas.tagCreateSchema>;
export type TagUpdateFormValues = z.infer<typeof zodSchemas.tagUpdateSchema>;
export type SpecialCreateFormValues = z.infer<
  typeof zodSchemas.specialCreateSchema
>;
export type SpecialUpdateFormValues = z.infer<
  typeof zodSchemas.specialUpdateSchema
>;
export type FeatureCreateFormValues = z.infer<
  typeof zodSchemas.featureCreateSchema
>;
export type FeatureUpdateFormValues = z.infer<
  typeof zodSchemas.featureUpdateSchema
>;
export type UserCreateFormValues = z.infer<typeof zodSchemas.userCreateSchema>;
export type UserUpdateFormValues = z.infer<typeof zodSchemas.userUpdateSchema>;
export type RoleCreateFormValues = z.infer<typeof zodSchemas.roleCreateSchema>;
export type RoleUpdateFormValues = z.infer<typeof zodSchemas.roleUpdateSchema>;

// Schema 类型（从 OpenAPI types 导出）
export type {
  ArticleLiteSchema as ArticleLiteValues,
  ArticleSchema as ArticleValues,
  CategoryLiteSchema as CategoryLiteValues,
  CategorySchema as CategoryValues,
  TagLiteSchema as TagLiteValues,
  TagSchema as TagValues,
  SpecialLiteSchema as SpecialLiteValues,
  SpecialSchema as SpecialValues,
  FeatureLiteSchema as FeatureLiteValues,
  FeatureSchema as FeatureValues,
  UserLiteSchema as UserLiteValues,
  UserSchema as UserValues,
  RoleLiteSchema as RoleLiteValues,
  RoleSchema as RoleValues,
} from "@/openapi/types.gen";
