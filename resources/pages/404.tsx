import { A } from "@solidjs/router";
import { Button } from "@/components/ui/button";
import { Home, ArrowLeft } from "lucide-solid";

export default function NotFoundPage() {
    return (
        <div class="flex min-h-[60vh] flex-col items-center justify-center text-center">
            {/* 404 数字 */}
            <div class="relative">
                <h1 class="text-[120px] font-bold leading-none text-muted-foreground/20 sm:text-[180px]">
                    404
                </h1>
                <div class="absolute inset-0 flex items-center justify-center">
                    <div class="space-y-2">
                        <h2 class="text-2xl font-semibold tracking-tight sm:text-3xl">
                            页面不存在
                        </h2>
                        <p class="text-muted-foreground">
                            您访问的页面可能已被移除或地址有误
                        </p>
                    </div>
                </div>
            </div>

            {/* 操作按钮 */}
            <div class="mt-8 flex gap-3">
                <Button variant="outline" onClick={() => window.history.back()}>
                    <ArrowLeft class="mr-2 h-4 w-4" />
                    返回上页
                </Button>
                <Button as={A} href="/">
                    <Home class="mr-2 h-4 w-4" />
                    返回首页
                </Button>
            </div>

            {/* 装饰元素 */}
            <div class="mt-12 flex items-center gap-2 text-xs text-muted-foreground">
                <span>错误代码: 404</span>
                <span>•</span>
                <span>Not Found</span>
            </div>
        </div>
    );
}
