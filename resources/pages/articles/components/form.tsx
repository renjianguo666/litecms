import { createResource, createMemo, Show } from "solid-js";
import { useWTForm } from "@/components/wtform";
import { Save, RotateCcw, Loader } from "lucide-solid";
import {
  ArticleCreateFormSchema,
  ArticleUpdateFormSchema,
  type ArticleCreateFormValues,
  type ArticleUpdateFormValues,
  category,
  tag,
  special,
  feature,
  upload,
} from "@/lib/api";
import { TreeList, type TreeNode } from "@/components/ui/tree-list";
import { TreeListMulti } from "@/components/ui/tree-list-multi";

// --- 这里是修改的核心部分 ---
interface CreateModeProps {
  mode: "create";
  defaultValues: ArticleCreateFormValues;
  onSubmit: (values: ArticleCreateFormValues) => Promise<void>;
  submitText?: string;
}

interface EditModeProps {
  mode: "edit";
  defaultValues: ArticleUpdateFormValues;
  onSubmit: (values: ArticleUpdateFormValues) => Promise<void>;
  submitText?: string;
}

type ArticleFormProps = CreateModeProps | EditModeProps;

export default function ArticleForm(props: ArticleFormProps) {
  // 生成 upload_token
  const uploadToken = Math.random().toString(36).slice(2) + Date.now().toString(36);

  // 获取栏目列表
  const [categories] = createResource(async () => {
    const res = await category.list({ page_size: 100 });
    return res.items ?? [];
  });

  // 获取标签列表
  const [tags] = createResource(async () => {
    const res = await tag.list({ page_size: 100 });
    return res.items ?? [];
  });

  // 获取专题列表
  const [specials] = createResource(async () => {
    const res = await special.list({ page_size: 100 });
    return res.items ?? [];
  });

  // 获取推荐位列表
  const [features] = createResource(async () => {
    const res = await feature.list({ page_size: 100 });
    return res.items ?? [];
  });

  const schema =
    props.mode === "create" ? ArticleCreateFormSchema : ArticleUpdateFormSchema;

  const form = useWTForm<ArticleCreateFormValues | ArticleUpdateFormValues>(
    () => ({
      defaultValues: props.defaultValues,
      validators: {
        onMount: schema,
        onChange: schema,
      },
      onSubmit: async ({ value }) => {
        if (props.mode === "create") {
          await props.onSubmit({
            ...value,
            upload_token: uploadToken,
          } as ArticleCreateFormValues);
        } else {
          await props.onSubmit({
            ...value,
            upload_token: uploadToken,
          } as ArticleUpdateFormValues);
        }
      },
    }),
  );

  // 图片上传处理
  const handleImageUpload = async (file: File): Promise<string> => {
    const result = await upload.upload(file, uploadToken);
    return result.url;
  };

  // 后端返回的是扁平树，直接使用 depth 做层级
  const categoryTreeNodes = createMemo<TreeNode[]>(() => {
    const items = categories() ?? [];
    if (items.length === 0) return [];

    // 计算每个节点的 has_children
    const parentIds = new Set(
      items.map((c) => c.parent_id).filter((id) => id !== null),
    );

    return items.map((c) => ({
      id: c.id,
      name: c.name,
      parent_id: c.parent_id ?? null,
      depth: c.depth,
      has_children: parentIds.has(c.id),
    }));
  });

  // 标签选项
  const tagOptions = () =>
    (tags() ?? []).map((t) => ({
      label: t.name,
      value: t.id,
    }));

  // 专题选项
  const specialOptions = () =>
    (specials() ?? []).map((t) => ({
      label: t.name,
      value: t.id,
    }));

  // 推荐位选项
  const featureOptions = () =>
    (features() ?? []).map((f) => ({
      label: f.name,
      value: f.id,
    }));

  return (
    <form.Form class="relative">
      {/* 主内容区域 */}
      <div class="lg:mr-68 space-y-4">
        {/* 文章标题和内容 */}
        <div class="bg-card rounded-lg border border-border shadow-sm">
          <div class="p-5 space-y-4">
            {/* 标题 */}
            <form.StringField name="title" placeholder="请输入文章标题" />
            <form.EditorField
              name="text"
              label="文章内容"
              placeholder="请输入文章内容..."
              minHeight="400px"
              showWordCount
              onImageUpload={handleImageUpload}
            />
          </div>
        </div>

        {/* 文章描述和封面 */}
        <div class="bg-card rounded-lg border border-border shadow-sm">
          <div class="p-5">
            <h2 class="text-base font-semibold mb-4">摘要与封面</h2>
            <div class="grid grid-cols-1 gap-4">
              <form.TextareaField
                name="description"
                label="文章描述"
                placeholder="简短描述文章内容（可选）"
                rows={3}
              />
              <form.StringField
                name="cover_url"
                label="封面图片"
                placeholder="请输入封面图片URL（可选）"
              />
              <div class="grid grid-cols-2 gap-4">
                <form.StringField
                  name="source"
                  label="来源"
                  placeholder="文章来源（可选）"
                />
                <form.StringField
                  name="author"
                  label="作者"
                  placeholder="作者名称（可选）"
                />
              </div>
            </div>
          </div>
        </div>

        {/* 标签、专题与推荐位 */}
        <div class="bg-card rounded-lg border border-border shadow-sm">
          <div class="p-5">
            <h2 class="text-base font-semibold mb-4">推送至</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* 标签多选 */}
              <form.ComboboxField
                name="tag_ids"
                label="标签"
                options={tagOptions()}
                placeholder="选择标签..."
                searchPlaceholder="搜索标签..."
              />

              {/* 专题多选 */}
              <form.ComboboxField
                name="special_ids"
                label="专题"
                options={specialOptions()}
                placeholder="选择专题..."
                searchPlaceholder="搜索专题..."
              />

              {/* 推荐位多选 */}
              <form.ComboboxField
                name="feature_ids"
                label="推荐位"
                options={featureOptions()}
                placeholder="选择推荐位..."
                searchPlaceholder="搜索推荐位..."
              />
            </div>
          </div>
        </div>

        {/* 操作按钮 */}
        {/* 操作按钮 */}
        <div class="flex items-center justify-between pt-2">
          {/* 左侧：发布时间 */}
          <form.AppField name="published_at">
            {(field) => (
              <div class="flex items-center gap-2">
                <label class="text-sm font-medium whitespace-nowrap">
                  发布时间
                </label>
                <input
                  type="datetime-local"
                  class="h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  value={(field().state.value as string)?.slice(0, 16) ?? ""}
                  onInput={(e) => {
                    const val = e.currentTarget.value;
                    field().handleChange(val ? `${val}:00Z` : null);
                  }}
                />
              </div>
            )}
          </form.AppField>

          {/* 右侧：按钮 */}
          <div class="flex gap-3">
            <form.ResetButton class="gap-2">
              <RotateCcw class="size-4" />
              重置
            </form.ResetButton>
            <form.SubmitButton class="gap-2">
              <Save class="size-4" />
              {props.submitText ?? "发布文章"}
            </form.SubmitButton>
          </div>
        </div>
      </div>

      {/* 右侧栏目侧边栏 - 固定定位 */}
      <aside class="hidden lg:block fixed right-6.5 top-20 bottom-4 w-64">
        <Show
          when={!categories.loading}
          fallback={
            <div class="h-full border border-border rounded-lg bg-card flex items-center justify-center">
              <Loader class="size-6 animate-spin text-muted-foreground" />
            </div>
          }
        >
          {props.mode === "create" ? (
            <form.AppField name="category_ids" mode="array">
              {(field) => (
                <TreeListMulti
                  nodes={categoryTreeNodes()}
                  value={(field().state.value as string[]) ?? []}
                  onChange={(val) => field().handleChange(val)}
                  title="选择栏目"
                  class="h-full shadow-sm"
                />
              )}
            </form.AppField>
          ) : (
            <form.AppField name="category_id">
              {(field) => (
                <TreeList
                  nodes={categoryTreeNodes()}
                  value={(field().state.value as string) ?? ""}
                  onChange={(val) => field().handleChange(val)}
                  title="选择栏目"
                  class="h-full shadow-sm"
                  allowEmpty={false}
                />
              )}
            </form.AppField>
          )}
        </Show>
      </aside>
    </form.Form>
  );
}
