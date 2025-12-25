import path from "path";
import { defineConfig } from "vite";
import solid from "vite-plugin-solid";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  base: "./",
  plugins: [solid(), tailwindcss()],
  publicDir: false,
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./resources"),
    },
  },
  build: {
    manifest: true,
    outDir: "public/build/",
    rollupOptions: {
      input: "/resources/main.tsx",
      output: {
        manualChunks: {
          // 把大型库单独打包
          "vendor-ui": ["@kobalte/core"],
          "vendor-editor": ["@tiptap/core", "@tiptap/starter-kit"],
          "vendor-table": ["@tanstack/solid-table"],
          "vendor-form": ["@tanstack/solid-form"],
        },
      },
    },
  },
  server: {
    watch: {
      // 【关键修复】忽略 templates 目录下的文件变更
      // 这样后端写入文件时，Vite 不会触发页面刷新
      ignored: ["**/application/**"],
    },
  },
});
