import { render } from "solid-js/web";
import { Router } from "@solidjs/router";
import { Suspense } from "solid-js";
import { Loader } from "lucide-solid";
import { ToastRegion } from "@/components/ui/toast";
import { getBasePathFromMeta } from "@/lib/utils";
import "./main.css";

import { AppRoutes } from "./routes";

const root = document.getElementById("root");
const basePath = getBasePathFromMeta();

render(
  () => (
    <Suspense
      fallback={
        <div class="min-h-screen flex items-center justify-center bg-muted">
          <Loader class="size-10 animate-spin text-primary" />
        </div>
      }
    >
      <ToastRegion>
        <Router base={basePath}>
          <AppRoutes />
        </Router>
      </ToastRegion>
    </Suspense>
  ),
  root!,
);

