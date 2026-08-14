import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { FluentProvider } from "@fluentui/react-components";
import { App } from "./App";
import { bankStyleTheme } from "./theme";

const container = document.getElementById("root");
if (!container) {
  throw new Error("루트 엘리먼트(#root)를 찾을 수 없습니다.");
}

createRoot(container).render(
  <StrictMode>
    <FluentProvider theme={bankStyleTheme}>
      <App />
    </FluentProvider>
  </StrictMode>,
);
