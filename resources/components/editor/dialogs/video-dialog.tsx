import { createSignal, type Accessor } from "solid-js";
import type { Editor } from "@tiptap/core";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  validateAndSanitizeUrl,
  convertToEmbedUrl,
  isValidEmbedUrl,
} from "../utils/security";
import { textareaClass } from "../utils/styles";

/**
 * 视频类型
 */
export type VideoType = "upload" | "embed";

/**
 * 视频对话框属性
 */
export interface VideoDialogProps {
  /** 是否打开 */
  open: boolean;
  /** 关闭回调 */
  onClose: () => void;
  /** 编辑器实例 */
  editor: Accessor<Editor | null>;
}

/**
 * 视频对话框组件
 *
 * 用于插入视频，支持嵌入视频（YouTube、Bilibili 等）和视频文件 URL。
 */
export function VideoDialog(props: VideoDialogProps) {
  const [videoUrl, setVideoUrl] = createSignal("");
  const [videoType, setVideoType] = createSignal<VideoType>("embed");

  // 对话框打开时重置状态
  const handleOpenChange = (open: boolean) => {
    if (open) {
      setVideoUrl("");
      setVideoType("embed");
    } else {
      props.onClose();
    }
  };

  // 插入视频
  const insertVideo = () => {
    const ed = props.editor();
    if (!ed) return;

    const url = videoUrl();
    const type = videoType();

    if (type === "embed") {
      let embedUrl = url;
      if (!isValidEmbedUrl(url)) {
        const converted = convertToEmbedUrl(url);
        if (converted) {
          embedUrl = converted;
        } else {
          alert("无法识别的视频链接格式");
          return;
        }
      }

      ed.chain().focus().setIframe({ src: embedUrl }).run();
    } else {
      const sanitizedUrl = validateAndSanitizeUrl(url);
      if (!sanitizedUrl) {
        alert("请输入有效的视频 URL");
        return;
      }

      ed.chain().focus().setVideo({ src: sanitizedUrl }).run();
    }

    props.onClose();
  };

  return (
    <Dialog open={props.open} onOpenChange={handleOpenChange}>
      <DialogContent class="max-w-md z-1001">
        <DialogHeader>
          <DialogTitle>插入视频</DialogTitle>
        </DialogHeader>
        <div class="space-y-4 py-4">
          {/* 视频类型切换 */}
          <div class="flex rounded-lg border border-border p-1 bg-muted">
            <button
              type="button"
              class={`flex-1 px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                videoType() === "embed"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
              onClick={() => setVideoType("embed")}
            >
              嵌入视频
            </button>
            <button
              type="button"
              class={`flex-1 px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                videoType() === "upload"
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
              onClick={() => setVideoType("upload")}
            >
              视频文件
            </button>
          </div>

          <div class="space-y-2">
            <label class="text-sm font-medium" for="editor-video-url">
              {videoType() === "embed" ? "视频链接" : "视频文件地址"}
            </label>
            <textarea
              id="editor-video-url"
              name="editor-video-url"
              class={`${textareaClass} h-24 leading-relaxed`}
              placeholder={
                videoType() === "embed"
                  ? "粘贴 YouTube、Bilibili、Vimeo 链接\n或 iframe 嵌入代码"
                  : "https://example.com/video.mp4"
              }
              value={videoUrl()}
              onInput={(e) => setVideoUrl(e.currentTarget.value)}
            />
            <p class="text-xs text-muted-foreground">
              {videoType() === "embed"
                ? "支持 YouTube、Bilibili、Vimeo"
                : "支持 mp4、webm 格式"}
            </p>
          </div>
        </div>
        <DialogFooter>
          <Button variant="secondary" onClick={props.onClose}>
            取消
          </Button>
          <Button disabled={!videoUrl()} onClick={insertVideo}>
            插入
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default VideoDialog;
