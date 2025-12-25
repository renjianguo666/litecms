import {
  ErrorBoundary as SolidErrorBoundary,
  type ParentProps,
} from "solid-js";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { AlertTriangle, RefreshCw } from "lucide-solid";

interface ErrorFallbackProps {
  error: Error;
  reset: () => void;
}

function ErrorFallback(props: ErrorFallbackProps) {
  return (
    <div class="flex min-h-[400px] items-center justify-center p-6">
      <Card class="max-w-md w-full">
        <CardHeader class="text-center">
          <div class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
            <AlertTriangle class="h-6 w-6 text-destructive" />
          </div>
          <CardTitle>页面出错了</CardTitle>
          <CardDescription>抱歉，页面加载时发生了错误</CardDescription>
        </CardHeader>
        <CardContent class="space-y-4">
          <div class="rounded-md bg-muted p-3">
            <code class="text-xs text-muted-foreground break-all">
              {props.error.message}
            </code>
          </div>
          <div class="flex justify-center gap-2">
            <Button variant="outline" onClick={() => window.location.reload()}>
              <RefreshCw class="mr-2 h-4 w-4" />
              刷新页面
            </Button>
            <Button onClick={props.reset}>重试</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export function ErrorBoundary(props: ParentProps) {
  return (
    <SolidErrorBoundary
      fallback={(error, reset) => <ErrorFallback error={error} reset={reset} />}
    >
      {props.children}
    </SolidErrorBoundary>
  );
}
