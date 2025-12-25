import { createResource, createMemo, Show } from "solid-js";
import { useWTForm } from "@/components/wtform";
import { Save, RotateCcw, Loader } from "lucide-solid";
import {
  CategoryCreateFormSchema,
  CategoryUpdateFormSchema,
  type CategoryCreateFormValues,
  type CategoryUpdateFormValues,
  category,
  template,
} from "@/lib/api";
import { TreeList, type TreeNode } from "@/components/ui/tree-list";
import { useSidebar } from "@/components/sidebar";

interface CreateModeProps {
  mode: "create";
  defaultValues: CategoryCreateFormValues;
  onSubmit: (values: CategoryCreateFormValues) => Promise<void>;
  submitText?: string;
  /** 编辑时禁用自己及子节点（不能选自己作为父栏目） */
  disabledId?: string;
}

interface EditModeProps {
  mode: "edit";
  defaultValues: CategoryUpdateFormValues;
  onSubmit: (values: CategoryUpdateFormValues) => Promise<void>;
  submitText?: string;
  /** 编辑时禁用自己及子节点（不能选自己作为父栏目） */
  disabledId?: string;
}

type CategoryFormProps = CreateModeProps | EditModeProps;

export default function CategoryForm(props: CategoryFormProps) {
  const { isOpen: sidebarOpen } = useSidebar();

  // 获取栏目列表用于父栏目选择
  const [categories] = createResource(async () => {
    const res = await category.list({ page_size: 100 });
    return res.items ?? [];
  });

  // 获取模板选项
  const [templateOptions] = createResource(() => template.options());

  // 模板选项
  const categoryTemplateOptions = () =>
    (templateOptions() ?? []).map((t) => ({
      label: t,
      value: t,
    }));

  const schema =
    props.mode === "create"
      ? CategoryCreateFormSchema
      : CategoryUpdateFormSchema;

  const form = useWTForm<CategoryCreateFormValues | CategoryUpdateFormValues>(
    () => ({
      defaultValues: props.defaultValues,
      validators: {
        onMount: schema,
        onChange: schema,
      },
      onSubmit: async ({ value }) => {
        if (props.mode === "create") {
          await props.onSubmit(value as CategoryCreateFormValues);
        } else {
          await props.onSubmit(value as CategoryUpdateFormValues);
        }
      },
    }),
  );

  // 将栏目数据转换为 TreeNode 格式
  const categoryNodes = createMemo<TreeNode[]>(() => {
    const items = categories() ?? [];
    if (items.length === 0) return [];

    // 计算每个节点的 has_children
    const parentIds = new Set(
      items
        .map((c) => c.parent_id)
        .filter((id) => id !== null && id !== undefined),
    );

    return items.map((c) => ({
      id: c.id,
      name: c.name,
      parent_id: c.parent_id ?? null,
      depth: c.depth,
      has_children: parentIds.has(c.id),
    }));
  });

  return (
    <form.Form class="relative">
      {/* 左侧栏目侧边栏 - 固定定位，响应侧边栏折叠状态 */}
      <aside
        class={`hidden lg:block fixed top-20 bottom-4 w-60 transition-[left] duration-300 ${sidebarOpen() ? "left-58" : "left-20"
          }`}
      >
        <Show
          when={!categories.loading}
          fallback={
            <div class="h-full border border-border rounded-lg bg-card flex items-center justify-center">
              <Loader class="size-6 animate-spin text-muted-foreground" />
            </div>
          }
        >
          <form.Field name="parent_id">
            {(field) => (
              <TreeList
                nodes={categoryNodes()}
                value={field().state.value as string | null}
                onChange={(val) => field().handleChange(val)}
                title="选择父级栏目"
                emptyLabel="顶级栏目"
                disabledId={props.disabledId}
                class="h-full shadow-sm"
              />
            )}
          </form.Field>
        </Show>
      </aside>

      {/* 主内容区域 */}
      <div class="lg:ml-65 space-y-4">
        {/* 小屏幕下的栏目选择（下拉形式） */}
        <div class="lg:hidden">
          <div class="bg-card rounded-lg border border-border shadow-sm">
            <div class="p-5">
              <h2 class="text-base font-semibold mb-4">父级栏目</h2>
              <form.SelectField
                name="parent_id"
                label="选择父级栏目"
                placeholder="作为顶级栏目"
                options={(categories() ?? []).map((c) => ({
                  label:
                    (c.depth > 0 ? "　".repeat(c.depth) + "› " : "") + c.name,
                  value: c.id,
                }))}
                nullable
              />
            </div>
          </div>
        </div>

        {/* 基本信息卡片 */}
        <div class="bg-card rounded-lg border border-border shadow-sm">
          <div class="p-5">
            <h2 class="text-base font-semibold mb-4">基本信息</h2>
            <div class="grid grid-cols-1 gap-4">
              <form.StringField
                name="name"
                label="名称"
                placeholder="请输入分类名称"
              />
              <form.StringField
                name="title"
                label="标题"
                placeholder="请输入分类标题（可选）"
              />
              <form.TextareaField
                name="description"
                label="描述"
                placeholder="请输入分类描述..."
                rows={3}
              />
              <form.StringField
                name="cover_url"
                label="封面图片"
                placeholder="请输入封面图片URL"
              />
            </div>
          </div>
        </div>

        {/* URL 设置卡片 */}
        <div class="bg-card rounded-lg border border-border shadow-sm">
          <div class="p-5">
            <h2 class="text-base font-semibold mb-4">高级设置</h2>
            <div class="grid grid-cols-1 gap-4">
              <form.StringField
                name="path"
                label="栏目路径"
                placeholder="如：/category/{key}"
                description="可用占位符{key}{year}{month}{day}{y}{m}{d}{parent}"
              />
              <form.StringField
                name="content_path"
                label="内容路径"
                placeholder="如：/p/{key}.html"
                description="可用占位符{key}{year}{month}{day}{y}{m}{d}{parent}"
              />
              <form.StringField
                name="domain"
                label="域名"
                description="绑定域名"
              />
            </div>
          </div>
        </div>

        {/* 显示设置卡片 */}
        <div class="bg-card rounded-lg border border-border shadow-sm">
          <div class="p-5">
            <h2 class="text-base font-semibold mb-4">显示设置</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <form.NumberField
                name="page_size"
                label="每页条数"
                placeholder="默认10条"
                min={1}
                max={100}
              />
              <form.NumberField
                name="priority"
                label="优先级"
                placeholder="数值越大越靠前"
                min={0}
              />
              <form.SelectField
                name="template"
                label="模板"
                placeholder="请选择模板"
                options={categoryTemplateOptions()}
                nullable={false}
              />

            </div>
          </div>
        </div>

        {/* 操作按钮 */}
        <div class="flex justify-end gap-3 pt-2">
          <form.ResetButton class="gap-2">
            <RotateCcw class="size-4" />
            重置
          </form.ResetButton>
          <form.SubmitButton class="gap-2">
            <Save class="size-4" />
            {props.submitText ?? "保存"}
          </form.SubmitButton>
        </div>
      </div>
    </form.Form>
  );
}
