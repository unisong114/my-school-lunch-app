// 백엔드 API 클라이언트. 프론트엔드는 오직 이 모듈을 통해서만 백엔드와 통신하며
// NEIS API를 직접 호출하지 않습니다.

import type {
  MealQueryResponse,
  SchoolSearchResponse,
} from "../types";

/** 백엔드가 반환한 오류를 표현하는 예외. */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

async function request<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { Accept: "application/json" },
    });
  } catch (cause) {
    throw new ApiError(
      "서버에 연결할 수 없습니다. 네트워크 상태를 확인해 주세요.",
      0,
    );
  }

  if (!response.ok) {
    let detail = "요청을 처리하지 못했습니다.";
    try {
      const body = (await response.json()) as { detail?: string };
      if (body?.detail) {
        detail = body.detail;
      }
    } catch {
      // 본문 파싱 실패는 무시하고 기본 메시지를 사용합니다.
    }
    throw new ApiError(detail, response.status);
  }

  return (await response.json()) as T;
}

/** 부분 학교명으로 학교를 검색합니다. */
export function searchSchools(name: string): Promise<SchoolSearchResponse> {
  const params = new URLSearchParams({ name });
  return request<SchoolSearchResponse>(`/api/schools?${params.toString()}`);
}

/** 급식 분석용 학교 샘플 10개를 불러옵니다. */
export function sampleSchools(): Promise<SchoolSearchResponse> {
  return request<SchoolSearchResponse>("/api/schools/sample");
}

/** 선택한 학교와 날짜 범위로 중식 급식을 조회합니다. */
export function fetchMeals(args: {
  eduOfficeCode: string;
  schoolCode: string;
  fromDate: string;
  toDate: string;
}): Promise<MealQueryResponse> {
  const params = new URLSearchParams({
    eduOfficeCode: args.eduOfficeCode,
    schoolCode: args.schoolCode,
    fromDate: args.fromDate,
    toDate: args.toDate,
  });
  return request<MealQueryResponse>(`/api/meals?${params.toString()}`);
}
