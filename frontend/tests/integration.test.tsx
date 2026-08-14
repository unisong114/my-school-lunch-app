import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { FluentProvider, webLightTheme } from "@fluentui/react-components";
import { describe, expect, it } from "vitest";
import { App } from "../src/App";
import { server } from "./mocks/server";

function renderApp() {
  return render(
    <FluentProvider theme={webLightTheme}>
      <App />
    </FluentProvider>,
  );
}

async function searchAndSelect(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText("학교 이름 검색"), "서울");
  await user.click(screen.getByRole("button", { name: "검색" }));
  const result = await screen.findByText("서울고등학교");
  await user.click(result);
}

describe("급식 조회 통합 흐름", () => {
  it("학교 검색 → 날짜 선택 → 급식 결과를 표시한다", async () => {
    const user = userEvent.setup();
    renderApp();

    await searchAndSelect(user);

    await user.type(screen.getByLabelText("시작일"), "2026-01-05");
    await user.type(screen.getByLabelText("종료일"), "2026-01-09");
    await user.click(screen.getByRole("button", { name: "급식 조회" }));

    const results = await screen.findByLabelText("급식 조회 결과");
    expect(within(results).getByText("백미밥")).toBeInTheDocument();
    expect(within(results).getByText("김치찌개")).toBeInTheDocument();
  });

  it("검색 결과가 없으면 안내 메시지를 표시한다", async () => {
    const user = userEvent.setup();
    renderApp();

    await user.type(screen.getByLabelText("학교 이름 검색"), "없는학교");
    await user.click(screen.getByRole("button", { name: "검색" }));

    expect(
      await screen.findByText(/검색 결과가 없습니다/),
    ).toBeInTheDocument();
  });

  it("시작일이 종료일보다 이후이면 조회를 막고 오류를 안내한다", async () => {
    const user = userEvent.setup();
    renderApp();

    await searchAndSelect(user);

    await user.type(screen.getByLabelText("시작일"), "2026-01-09");
    await user.type(screen.getByLabelText("종료일"), "2026-01-05");
    await user.click(screen.getByRole("button", { name: "급식 조회" }));

    expect(
      await screen.findByText(/시작일은 종료일보다 이후일 수 없습니다/),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText("급식 조회 결과")).not.toBeInTheDocument();
  });

  it("급식 정보가 없으면 안내 메시지를 표시한다", async () => {
    const user = userEvent.setup();
    server.use(
      http.get("/api/meals", () =>
        HttpResponse.json({
          schoolCode: "7010569",
          fromDate: "2026-01-05",
          toDate: "2026-01-09",
          meals: [],
        }),
      ),
    );
    renderApp();

    await searchAndSelect(user);
    await user.type(screen.getByLabelText("시작일"), "2026-01-05");
    await user.type(screen.getByLabelText("종료일"), "2026-01-09");
    await user.click(screen.getByRole("button", { name: "급식 조회" }));

    expect(
      await screen.findByText(/급식 정보가 없습니다/),
    ).toBeInTheDocument();
  });

  it("백엔드 오류 시 오류 메시지를 표시한다", async () => {
    const user = userEvent.setup();
    server.use(
      http.get("/api/meals", () =>
        HttpResponse.json(
          { detail: "급식 정보를 불러오지 못했습니다." },
          { status: 502 },
        ),
      ),
    );
    renderApp();

    await searchAndSelect(user);
    await user.type(screen.getByLabelText("시작일"), "2026-01-05");
    await user.type(screen.getByLabelText("종료일"), "2026-01-09");
    await user.click(screen.getByRole("button", { name: "급식 조회" }));

    await waitFor(() =>
      expect(
        screen.getByText(/급식 정보를 불러오지 못했습니다/),
      ).toBeInTheDocument(),
    );
  });
});
