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

export const SAMPLE_SCHOOLS: School[] = [
  SEOUL_HIGH,
  {
    eduOfficeCode: "B10",
    eduOfficeName: "서울특별시교육청",
    schoolCode: "7010568",
    schoolName: "한강중학교",
    schoolKind: "중학교",
    region: "서울특별시",
    address: "서울특별시 용산구 한강대로",
  },
  {
    eduOfficeCode: "D10",
    eduOfficeName: "대전광역시교육청",
    schoolCode: "7340072",
    schoolName: "한밭초등학교",
    schoolKind: "초등학교",
    region: "대전광역시",
    address: "대전광역시 서구 계룡로",
  },
  {
    eduOfficeCode: "J10",
    eduOfficeName: "경기도교육청",
    schoolCode: "7531001",
    schoolName: "수원과학고등학교",
    schoolKind: "고등학교",
    region: "경기도",
    address: "경기도 수원시 장안구",
  },
  {
    eduOfficeCode: "C10",
    eduOfficeName: "부산광역시교육청",
    schoolCode: "7120038",
    schoolName: "해운대중학교",
    schoolKind: "중학교",
    region: "부산광역시",
    address: "부산광역시 해운대구",
  },
  {
    eduOfficeCode: "E10",
    eduOfficeName: "광주광역시교육청",
    schoolCode: "7380049",
    schoolName: "빛고을초등학교",
    schoolKind: "초등학교",
    region: "광주광역시",
    address: "광주광역시 북구",
  },
  {
    eduOfficeCode: "G10",
    eduOfficeName: "강원특별자치도교육청",
    schoolCode: "7810099",
    schoolName: "춘천고등학교",
    schoolKind: "고등학교",
    region: "강원특별자치도",
    address: "강원특별자치도 춘천시",
  },
  {
    eduOfficeCode: "M10",
    eduOfficeName: "전라북도교육청",
    schoolCode: "8220131",
    schoolName: "전주중앙중학교",
    schoolKind: "중학교",
    region: "전북특별자치도",
    address: "전북특별자치도 전주시",
  },
  {
    eduOfficeCode: "P10",
    eduOfficeName: "제주특별자치도교육청",
    schoolCode: "9290005",
    schoolName: "제주남초등학교",
    schoolKind: "초등학교",
    region: "제주특별자치도",
    address: "제주특별자치도 제주시",
  },
  {
    eduOfficeCode: "K10",
    eduOfficeName: "충청남도교육청",
    schoolCode: "8140041",
    schoolName: "천안북고등학교",
    schoolKind: "고등학교",
    region: "충청남도",
    address: "충청남도 천안시",
  },
];

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
    const matches = SAMPLE_SCHOOLS.filter((school) =>
      school.schoolName.includes(name),
    );
    return HttpResponse.json({
      schools: matches.length > 0 ? matches : [SEOUL_HIGH],
    });
  }),
  http.get("/api/schools/sample", () => {
    return HttpResponse.json({ schools: SAMPLE_SCHOOLS });
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
