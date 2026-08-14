import { test, expect, type Page } from "@playwright/test";

// 백엔드 API를 네트워크 경계에서 스텁하여 프론트엔드 전체 사용자 흐름을
// 안정적으로 검증합니다. (NEIS 실데이터에 의존하지 않음)

const SEOUL_HIGH = {
  eduOfficeCode: "B10",
  eduOfficeName: "서울특별시교육청",
  schoolCode: "7010569",
  schoolName: "서울고등학교",
  schoolKind: "고등학교",
  region: "서울특별시",
  address: "서울특별시 서초구 남부순환로",
};

const MEALS = [
  {
    date: "2026-01-05",
    mealName: "중식",
    dishes: [
      { name: "백미밥", allergies: [] as number[] },
      { name: "김치찌개", allergies: [5, 9] },
    ],
    calorie: "700 Kcal",
    nutrition: null,
    origin: null,
  },
];

async function stubBackend(
  page: Page,
  options: { schools?: unknown[]; meals?: unknown[]; mealStatus?: number } = {},
) {
  await page.route("**/api/schools**", async (route) => {
    const name = new URL(route.request().url()).searchParams.get("name") ?? "";
    const schools =
      options.schools ?? (name.includes("없는") ? [] : [SEOUL_HIGH]);
    await route.fulfill({ json: { schools } });
  });

  await page.route("**/api/meals**", async (route) => {
    if (options.mealStatus && options.mealStatus >= 400) {
      await route.fulfill({
        status: options.mealStatus,
        json: { detail: "급식 정보를 불러오지 못했습니다." },
      });
      return;
    }
    await route.fulfill({
      json: {
        schoolCode: SEOUL_HIGH.schoolCode,
        fromDate: "2026-01-05",
        toDate: "2026-01-09",
        meals: options.meals ?? MEALS,
      },
    });
  });
}

test("학교 검색 → 날짜 선택 → 급식 결과 표시", async ({ page }) => {
  await stubBackend(page);
  await page.goto("/");

  await page.getByLabel("학교 이름 검색").fill("서울");
  await page.getByRole("button", { name: "검색" }).click();

  await page.getByText("서울고등학교").click();

  await page.getByLabel("시작일").fill("2026-01-05");
  await page.getByLabel("종료일").fill("2026-01-09");
  await page.getByRole("button", { name: "급식 조회" }).click();

  const results = page.getByLabel("급식 조회 결과");
  await expect(results.getByText("백미밥")).toBeVisible();
  await expect(results.getByText("김치찌개")).toBeVisible();
});

test("검색 결과가 없으면 안내 메시지를 표시한다", async ({ page }) => {
  await stubBackend(page);
  await page.goto("/");

  await page.getByLabel("학교 이름 검색").fill("없는학교");
  await page.getByRole("button", { name: "검색" }).click();

  await expect(page.getByText(/검색 결과가 없습니다/)).toBeVisible();
});

test("잘못된 날짜 범위는 조회 전에 차단된다", async ({ page }) => {
  await stubBackend(page);
  await page.goto("/");

  await page.getByLabel("학교 이름 검색").fill("서울");
  await page.getByRole("button", { name: "검색" }).click();
  await page.getByText("서울고등학교").click();

  await page.getByLabel("시작일").fill("2026-01-09");
  await page.getByLabel("종료일").fill("2026-01-05");
  await page.getByRole("button", { name: "급식 조회" }).click();

  await expect(
    page.getByText(/시작일은 종료일보다 이후일 수 없습니다/),
  ).toBeVisible();
  await expect(page.getByLabel("급식 조회 결과")).toHaveCount(0);
});

test("급식 정보가 없으면 안내 메시지를 표시한다", async ({ page }) => {
  await stubBackend(page, { meals: [] });
  await page.goto("/");

  await page.getByLabel("학교 이름 검색").fill("서울");
  await page.getByRole("button", { name: "검색" }).click();
  await page.getByText("서울고등학교").click();

  await page.getByLabel("시작일").fill("2026-01-05");
  await page.getByLabel("종료일").fill("2026-01-09");
  await page.getByRole("button", { name: "급식 조회" }).click();

  await expect(page.getByText(/급식 정보가 없습니다/)).toBeVisible();
});
