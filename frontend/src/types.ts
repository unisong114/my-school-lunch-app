// 내부 API(src/openapi.json) 계약에 대응하는 타입 정의.

export interface School {
  eduOfficeCode: string;
  eduOfficeName: string;
  schoolCode: string;
  schoolName: string;
  schoolKind?: string | null;
  region?: string | null;
  address?: string | null;
}

export interface SchoolSearchResponse {
  schools: School[];
}

export interface MealDish {
  name: string;
  allergies: number[];
}

export interface DailyMeal {
  date: string;
  mealName: string;
  dishes: MealDish[];
  calorie?: string | null;
  nutrition?: string | null;
  origin?: string | null;
}

export interface MealQueryResponse {
  schoolCode: string;
  fromDate: string;
  toDate: string;
  meals: DailyMeal[];
}

export interface LunchAnalysisArea {
  score: number;
  weightedScore: number;
  rationale: string;
}

/** 급식 배틀 백엔드(`agent/`)가 사용하는 평가 영역 키. */
export type LunchAnalysisAreaKey =
  | "nutritionBalance"
  | "healthiness"
  | "menuQuality"
  | "mealParticipation";

export interface LunchBattleSchoolResult {
  eduOfficeCode: string;
  schoolCode: string;
  schoolName: string;
  totalScore: number;
  areas: Record<LunchAnalysisAreaKey, LunchAnalysisArea>;
}

export interface LunchBattleResult {
  schoolA: LunchBattleSchoolResult;
  schoolB: LunchBattleSchoolResult;
  winner: "A" | "B" | "tie";
  summary: string;
  qualityNotes: string[];
}

export interface LunchAnalysisStateSchool {
  eduOfficeCode: string;
  schoolCode: string;
  schoolName: string;
}

export interface LunchAnalysisRequestMessage {
  role: "user";
  content: string;
}

export interface LunchAnalysisRequestState {
  schoolA: LunchAnalysisStateSchool;
  schoolB: LunchAnalysisStateSchool;
  date: string;
  prompt: string;
}

export interface LunchAnalysisRequest {
  thread_id: string;
  run_id: string;
  messages: LunchAnalysisRequestMessage[];
  state: LunchAnalysisRequestState;
}
