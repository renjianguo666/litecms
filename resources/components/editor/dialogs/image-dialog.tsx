import { createSignal, Show, type Accessor } from "solid-js";
import type { Editor } from "@tiptap/core";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Loader } from "lucide-solid";
import { validateAndSanitizeUrl } from "../utils/security";
import { inputClass } from "../utils/styles";

/**
 * 图片对话框属性
 */
export interface ImageDialogProps {
  /** 是否打开 */
  open: boolean;
  /** 关闭回调 */
  onClose: () => void;
  /** 编辑器实例 */
  editor: Accessor<Editor | null>;
  /** 图片上传回调 */
  onImageUpload?: (file: File) => Promise<string>;
}

/**
 * 图片对话框组件
 *
 * 用于插入图片，支持 URL 输入和本地上传。
 */
export function ImageDialog(props: ImageDialogProps) {
  const [imageUrl, setImageUrl] = createSignal("");
  const [imageAlt, setImageAlt] = createSignal("");
  const [isUploading, setIsUploading] = createSignal(false);

  let fileInputRef: HTMLInputElement | undefined;

  // 对话框打开时重置状态
  const handleOpenChange = (open: boolean) => {
    if (open) {
      setImageUrl("");
      setImageAlt("");
    } else {
      props.onClose();
    }
  };

  // 插入图片（URL 方式）
  const insertImage = () => {
    const ed = props.editor();
    if (!ed) return;

    const url = imageUrl();
    const alt = imageAlt();
    const sanitizedUrl = validateAndSanitizeUrl(url);

    if (!sanitizedUrl) {
      alert("请输入有效的图片 URL");
      return;
    }

    ed.chain().focus().setImage({ src: sanitizedUrl, alt }).run();
    props.onClose();
  };

  // 处理图片文件上传
  const handleImageUpload = async (file: File) => {
    if (!props.onImageUpload) return;

    const ed = props.editor();
    if (!ed) return;

    // 验证文件类型
    if (!file.type.startsWith("image/")) {
      alert("请选择图片文件");
      return;
    }

    // 验证文件大小（最大 10MB）
    if (file.size > 10 * 1024 * 1024) {
      alert("图片大小不能超过 10MB");
      return;
    }

    try {
      setIsUploading(true);
      const url = await props.onImageUpload(file);

      if (url) {
        ed.chain()
          .focus()
          .setImage({ src: url, alt: imageAlt() || file.name })
          .run();
        props.onClose();
      }
    } catch (error) {
      console.error("图片上传失败:", error);
      alert("图片上传失败，请重试");
    } finally {
      setIsUploading(false);
    }
  };

  // 文件选择处理
  const handleFileSelect = (e: Event) => {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (file) {
      handleImageUpload(file);
    }
    // 重置 input 以便可以选择同一文件
    input.value = "";
  };

  return (
    <Dialog open={props.open} onOpenChange={handleOpenChange}>
      <DialogContent class="max-w-md z-1001">
        <DialogHeader>
          <DialogTitle>插入图片</DialogTitle>
        </DialogHeader>
        <div class="space-y-4 py-4">
          {/* 本地上传（如果支持） */}
          <Show when={props.onImageUpload}>
            <div class="space-y-2">
              <label class="text-sm font-medium" for="editor-image-file">
                本地上传
              </label>
              <input
                ref={fileInputRef}
                id="editor-image-file"
                name="editor-image-file"
                type="file"
                accept="image/*"
                class="w-full h-10 px-3 py-2 text-sm bg-background border border-input rounded-md file:border-0 file:bg-transparent file:text-sm file:font-medium cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                onChange={handleFileSelect}
                disabled={isUploading()}
              />
              <Show when={isUploading()}>
                <div class="flex items-center gap-2 text-sm text-primary">
                  <Loader class="size-4 animate-spin" />
                  上传中...
                </div>
              </Show>
            </div>
            <div class="relative">
              <div class="absolute inset-0 flex items-center">
                <div class="w-full border-t border-border" />
              </div>
              <div class="relative flex justify-center text-xs">
                <span class="bg-card px-2 text-muted-foreground">或</span>
              </div>
            </div>
          </Show>

          <div class="space-y-2">
            <label class="text-sm font-medium" for="editor-image-url">
              图片地址
            </label>
            <input
              id="editor-image-url"
              name="editor-image-url"
              type="url"
              class={inputClass}
              placeholder="https://example.com/image.jpg"
              value={imageUrl()}
              onInput={(e) => setImageUrl(e.currentTarget.value)}
              disabled={isUploading()}
            />
          </div>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <label class="text-sm font-medium" for="editor-image-alt">
                替代文本
              </label>
              <span class="text-xs text-muted-foreground">可选</span>
            </div>
            <input
              id="editor-image-alt"
              name="editor-image-alt"
              type="text"
              class={inputClass}
              placeholder="图片描述"
              value={imageAlt()}
              onInput={(e) => setImageAlt(e.currentTarget.value)}
              disabled={isUploading()}
            />
          </div>
        </div>
        <DialogFooter>
          <Button
            variant="secondary"
            onClick={props.onClose}
            disabled={isUploading()}
          >
            取消
          </Button>
          <Button
            onClick={insertImage}
            disabled={isUploading() || !imageUrl()}
          >
            插入
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default ImageDialog;
