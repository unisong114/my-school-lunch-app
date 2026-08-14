import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { FluentProvider } from "@fluentui/react-components";
import { describe, expect, it } from "vitest";
import { App } from "../src/App";
import { bankStyleTheme } from "../src/theme";
import { server } from "./mocks/server";

function renderApp() {
  return render(
    <FluentProvider theme={bankStyleTheme}>
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

function formatDateInput(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

async function openAnalysisTab(user: ReturnType<typeof userEvent.setup>) {
  renderApp();
  await user.click(screen.getByRole("tab", { name: "급식 분석" }));
  expect(await screen.findByText("한강중학교")).toBeInTheDocument();
}

describe("급식 조회 통합 흐름", () => {
  it("일부 키워드만 입력하면 버튼 클릭 없이 자동으로 검색 결과가 표시된다", async () => {
    const user = userEvent.setup();
    renderApp();

    await user.type(screen.getByLabelText("학교 이름 검색"), "서울");

    expect(
      await screen.findByText("서울고등학교", undefined, { timeout: 2000 }),
    ).toBeInTheDocument();
  });

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

it("급식 분석 페이지에서 샘플 학교를 보여주고 2곳까지만 선택할 수 있다", async () => {
  const user = userEvent.setup();

  await openAnalysisTab(user);

  expect(screen.getByText("선택된 학교: 0 / 2")).toBeInTheDocument();
  expect(screen.getByText("서울고등학교")).toBeInTheDocument();
  expect(screen.getByText("한밭초등학교")).toBeInTheDocument();

  await user.click(screen.getByText("서울고등학교"));
  await user.click(screen.getByText("한강중학교"));

  expect(screen.getByText("선택된 학교: 2 / 2")).toBeInTheDocument();
  expect(screen.getByText("A · 서울고등학교")).toBeInTheDocument();
  expect(screen.getByText("B · 한강중학교")).toBeInTheDocument();

  const thirdSchoolCard = screen
    .getByText("한밭초등학교")
    .closest('[role="button"]');
  expect(thirdSchoolCard).toHaveAttribute("aria-disabled", "true");

  await user.click(screen.getByRole("button", { name: "분석 시작" }));
  expect(
    await screen.findByText("분석 날짜를 선택해 주세요."),
  ).toBeInTheDocument();
});

it("분석 날짜는 이번달/직전달 범위로 제한된다", async () => {
  const user = userEvent.setup();
  const today = new Date();
  const currentMonthStart = formatDateInput(
    new Date(today.getFullYear(), today.getMonth(), 1),
  );
  const currentMonthEnd = formatDateInput(
    new Date(today.getFullYear(), today.getMonth(), today.getDate()),
  );
  const previousMonthStart = formatDateInput(
    new Date(today.getFullYear(), today.getMonth() - 1, 1),
  );
  const previousMonthEnd = formatDateInput(
    new Date(today.getFullYear(), today.getMonth(), 0),
  );

  await openAnalysisTab(user);

  const dateInput = screen.getByLabelText("분석 날짜");
  expect(dateInput).toHaveAttribute("min", currentMonthStart);
  expect(dateInput).toHaveAttribute("max", currentMonthEnd);

  await user.click(screen.getByLabelText("직전달"));
  expect(dateInput).toHaveAttribute("min", previousMonthStart);
  expect(dateInput).toHaveAttribute("max", previousMonthEnd);
});

it("학교 2곳과 날짜를 선택하면 기본 분석 프롬프트가 생성되고 수정할 수 있다", async () => {
  const user = userEvent.setup();

  await openAnalysisTab(user);

  await user.click(screen.getByText("서울고등학교"));
  await user.click(screen.getByText("한강중학교"));
  await user.type(screen.getByLabelText("분석 날짜"), "2026-08-12");

  const promptField = screen.getByLabelText("분석 요청문");
  expect(promptField).toHaveValue(
    "서울고등학교와 한강중학교의 2026년 8월 12일 중식 급식을 EVALUATION_RUBRIC.md 기준(영양 균형, 건강성, 식재료 및 메뉴 품질, 급식 참여도)으로 비교 평가해 주세요.",
  );

  await user.clear(promptField);
  await user.type(promptField, "두 학교의 선호도 차이도 함께 설명해 주세요.");
  expect(promptField).toHaveValue("두 학교의 선호도 차이도 함께 설명해 주세요.");
});
