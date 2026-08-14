import { defineConfig, devices } from "@playwright/test";

// E2E 대상 프론트엔드 주소. 기본값은 로컬 vite preview 서버입니다.
const baseURL = process.env.E2E_BASE_URL ?? "http://localhost:4173";

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  reporter: process.env.CI ? "list" : [["list"]],
  use: {
    baseURL,
    trace: "on-first-retry",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  // E2E_BASE_URL 이 지정되지 않으면 프론트엔드 preview 서버를 자동 기동합니다.
  webServer: process.env.E2E_BASE_URL
    ? undefined
    : {
        command: "npm --prefix ../frontend run preview -- --port 4173",
        url: baseURL,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      },
});
