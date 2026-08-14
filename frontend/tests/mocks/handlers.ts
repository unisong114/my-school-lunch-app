import { http, HttpResponse } from "msw";
import type { DailyMeal, School } from "../../src/types";

export const SEOUL_HIGH: School = {
  eduOfficeCode: "B10",
  eduOfficeName: "서울특별시교육청",
  schoolCode: "7010569",
  schoolName: "서울고등학교",
  schoolKind: "고등학교",
  region: "서울특별시",
  address: "서울특별시 서초구 남부순환로",
};

export const SAMPLE_MEALS: DailyMeal[] = [
  {
    date: "2026-01-05",
    mealName: "중식",
    dishes: [
      { name: "백미밥", allergies: [] },
      { name: "김치찌개", allergies: [5, 9] },
    ],
    calorie: "700 Kcal",
    nutrition: null,
    origin: null,
  },
];

// 기본 핸들러: 정상 흐름을 모킹합니다. 개별 테스트에서 server.use 로 덮어씁니다.
export const handlers = [
  http.get("/api/schools", ({ request }) => {
    const name = new URL(request.url).searchParams.get("name") ?? "";
    if (name.includes("없는")) {
      return HttpResponse.json({ schools: [] });
    }
    return HttpResponse.json({ schools: [SEOUL_HIGH] });
  }),
  http.get("/api/meals", () => {
    return HttpResponse.json({
      schoolCode: SEOUL_HIGH.schoolCode,
      fromDate: "2026-01-05",
      toDate: "2026-01-09",
      meals: SAMPLE_MEALS,
    });
  }),
];
