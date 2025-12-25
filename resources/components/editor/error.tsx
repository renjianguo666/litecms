import { ErrorBoundary as SolidErrorBoundary, type JSX } from "solid-js";
import { TriangleAlert, RefreshCw } from "lucide-solid";
import { Button } from "@/components/ui/button";

interface EditorErrorBoundaryProps {
  children: JSX.Element;
  onReset?: () => void;
}

/**
 * 编辑器错误边界组件
 */
export function EditorErrorBoundary(props: EditorErrorBoundaryProps) {
  return (
    <SolidErrorBoundary
      fallback={(err, reset) => (
        <EditorErrorFallback
          error={err}
          onReset={() => {
            reset();
            props.onReset?.();
          }}
        />
      )}
    >
      {props.children}
    </SolidErrorBoundary>
  );
}

interface EditorErrorFallbackProps {
  error: Error;
  onReset: () => void;
}

/**
 * 错误回退 UI
 */
function EditorErrorFallback(props: EditorErrorFallbackProps) {
  return (
    <div class="border border-destructive/50 rounded-lg p-6 bg-destructive/5">
      <div class="flex items-start gap-4">
        <div class="shrink-0">
          <TriangleAlert class="w-8 h-8 text-destructive" />
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="text-lg font-semibold text-destructive mb-2">
            编辑器加载失败
          </h3>
          <p class="text-muted-foreground mb-4">
            编辑器组件发生错误，请尝试刷新页面或重置编辑器。
          </p>

          {/* 错误详情 */}
          <details class="mb-4">
            <summary class="cursor-pointer text-sm text-muted-foreground hover:text-muted-foreground">
              查看错误详情
            </summary>
            <pre class="mt-2 p-3 bg-muted rounded text-xs overflow-auto max-h-32">
              {props.error.message}
              {props.error.stack && (
                <>
                  {"\n\n"}
                  {props.error.stack}
                </>
              )}
            </pre>
          </details>

          <Button variant="default" size="sm" onClick={props.onReset}>
            <RefreshCw class="w-4 h-4" />
            重试
          </Button>
        </div>
      </div>
    </div>
  );
}

export default EditorErrorBoundary;
