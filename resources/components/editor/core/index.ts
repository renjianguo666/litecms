/**
 * 核心扩展模块入口
 * 导出所有 Tiptap 扩展配置
 */

export { Video } from "./video-node";
export { Iframe } from "./iframe-node";
export { getDefaultExtensions } from "./extensions";

// 类型扩展声明
declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    video: {
      setVideo: (options: {
        src: string;
        width?: string;
        height?: string;
      }) => ReturnType;
    };
    iframe: {
      setIframe: (options: {
        src: string;
        width?: string;
        height?: string;
      }) => ReturnType;
    };
  }
}
