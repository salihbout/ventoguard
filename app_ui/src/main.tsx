import { DesignSystemProvider } from "@databricks/design-system";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { App } from "./App";
import "@databricks/design-system/index.css";
import "@databricks/design-system/fonts/dm-sans.css";
import "@databricks/design-system/fonts/dm-mono.css";
import "./styles/brand-tokens.css";
import "./styles/app.css";

const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: 60_000, retry: 1, refetchOnWindowFocus: false } } });

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <DesignSystemProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </QueryClientProvider>
    </DesignSystemProvider>
  </React.StrictMode>,
);
