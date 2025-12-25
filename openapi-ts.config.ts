import { defineConfig } from "@hey-api/openapi-ts";

export default defineConfig({
  // 指向你的 OpenAPI json 文件或 URL
  input: "openapi.json",

  // 生成文件的输出目录
  output: "resources/openapi",

  // 选择 Fetch 客户端 (最适合现代前端)
  client: "@hey-api/client-fetch",

  plugins: [
    {
      name: "zod",
      output: "zod.ts",
      definitions: {
        name: "{{name}}",
      },
    },
    {
      name: "@hey-api/sdk",
      asClass: false, // 推荐：使用函数式风格，利于 Tree-shaking
    },
    {
      name: "@hey-api/typescript",
      readOnlyWriteOnlyBehavior: "off",
    }

  ],
});
