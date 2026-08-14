import { afterEach, describe, expect, it, vi } from "vitest";
import { streamLunchAnalysis } from "../src/api/agentClient";
import { ApiError } from "../src/api/client";
import type { LunchBattleResult, School } from "../src/types";

const SCHOOL_A: School = {
  eduOfficeCode: "B10",
  eduOfficeName: "서울특별시교육청",
  schoolCode: "7010569",
  schoolName: "서울고등학교",
  schoolKind: "고등학교",
  region: "서울특별시",
  address: "서울특별시 서초구 남부순환로",
};

const SCHOOL_B: School = {
  eduOfficeCode: "D10",
  eduOfficeName: "대전광역시교육청",
  schoolCode: "7340072",
  schoolName: "한밭초등학교",
  schoolKind: "초등학교",
  region: "대전광역시",
  address: "대전광역시 서구 계룡로",
};

const SAMPLE_RESULT: LunchBattleResult = {
  schoolA: {
    eduOfficeCode: SCHOOL_A.eduOfficeCode,
    schoolCode: SCHOOL_A.schoolCode,
    schoolName: "서울고등학교",
    totalScore: 82.5,
    areas: {
      nutritionBalance: {
        score: 4,
        weightedScore: 32,
        rationale: "탄수화물과 단백질 구성이 균형적입니다.",
      },
      healthiness: {
        score: 4,
        weightedScore: 20,
        rationale: "튀김 비중이 낮고 채소 반찬이 포함됩니다.",
      },
      menuQuality: {
        score: 4,
        weightedScore: 16,
        rationale: "계절 식재료를 사용한 메뉴 구성이 돋보입니다.",
      },
      mealParticipation: {
        score: 5,
        weightedScore: 15,
        rationale: "학생 선호 메뉴와 균형을 잘 맞췄습니다.",
      },
    },
  },
  schoolB: {
    eduOfficeCode: SCHOOL_B.eduOfficeCode,
    schoolCode: SCHOOL_B.schoolCode,
    schoolName: "한밭초등학교",
    totalScore: 79,
    areas: {
      nutritionBalance: {
        score: 4,
        weightedScore: 32,
        rationale: "곡류와 단백질 조합은 양호합니다.",
      },
      healthiness: {
        score: 4,
        weightedScore: 20,
        rationale: "가공식품 비중이 약간 높습니다.",
      },
      menuQuality: {
        score: 3,
        weightedScore: 12,
        rationale: "식재료 정보가 제한적입니다.",
      },
      mealParticipation: {
        score: 5,
        weightedScore: 15,
        rationale: "학생 선호도가 높은 구성입니다.",
      },
    },
  },
  winner: "A",
  summary: "서울고등학교가 전반적으로 더 균형 잡힌 구성을 보였습니다.",
  qualityNotes: ["실제 배식량 정보는 포함되지 않았습니다."],
};

function createSseResponse(chunks: string[]): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });

  return new Response(stream, {
    status: 200,
    headers: { "Content-Type": "text/event-stream" },
  });
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("streamLunchAnalysis", () => {
  it("진행 상황 텍스트를 누적하고 최종 분석 결과를 전달한다", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        createSseResponse([
          'data: {"type":"RUN_STARTED"}\n\n',
          'data: {"type":"TEXT_MESSAGE_START"}\n\n',
          'data: {"type":"TEXT_MESSAGE_CONTENT","delta":"분석"}\n\n',
          'data: {"type":"TEXT_MESSAGE_CONTENT","delta":" 중"}\n\n',
          `data: ${JSON.stringify({ type: "CUSTOM", value: SAMPLE_RESULT })}\n\n`,
          'data: {"type":"RUN_FINISHED"}\n\n',
        ]),
      );

    const progressUpdates: string[] = [];
    const results: LunchBattleResult[] = [];
    const errors: string[] = [];

    await streamLunchAnalysis(
      {
        schoolA: SCHOOL_A,
        schoolB: SCHOOL_B,
        date: "2026-08-12",
        prompt: "두 학교의 급식을 비교해 주세요.",
        threadId: "thread-1",
        runId: "run-1",
      },
      {
        onProgress: (text) => progressUpdates.push(text),
        onResult: (result) => results.push(result),
        onError: (message) => errors.push(message),
      },
    );

    expect(progressUpdates).toEqual(["분석", "분석 중"]);
    expect(results).toEqual([SAMPLE_RESULT]);
    expect(errors).toEqual([]);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [, init] = fetchMock.mock.calls[0];
    expect(init?.method).toBe("POST");
    expect(init?.headers).toEqual({
      Accept: "text/event-stream",
      "Content-Type": "application/json",
    });
    expect(JSON.parse(String(init?.body))).toEqual({
      thread_id: "thread-1",
      run_id: "run-1",
      messages: [{ role: "user", content: "두 학교의 급식을 비교해 주세요." }],
      state: {
        schoolA: {
          eduOfficeCode: SCHOOL_A.eduOfficeCode,
          schoolCode: SCHOOL_A.schoolCode,
          schoolName: SCHOOL_A.schoolName,
        },
        schoolB: {
          eduOfficeCode: SCHOOL_B.eduOfficeCode,
          schoolCode: SCHOOL_B.schoolCode,
          schoolName: SCHOOL_B.schoolName,
        },
        date: "2026-08-12",
        prompt: "두 학교의 급식을 비교해 주세요.",
      },
    });
  });

  it("RUN_ERROR 이벤트를 ApiError로 전파하고 오류 콜백을 호출한다", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      createSseResponse([
        'data: {"type":"RUN_STARTED"}\n\n',
        'data: {"type":"RUN_ERROR","message":"분석 서버 내부 오류"}\n\n',
      ]),
    );

    const errors: string[] = [];

    await expect(
      streamLunchAnalysis(
        {
          schoolA: SCHOOL_A,
          schoolB: SCHOOL_B,
          date: "2026-08-12",
          prompt: "오류 테스트",
          threadId: "thread-2",
          runId: "run-2",
        },
        {
          onProgress: () => {},
          onResult: () => {},
          onError: (message) => errors.push(message),
        },
      ),
    ).rejects.toBeInstanceOf(ApiError);

    expect(errors).toEqual(["분석 서버 내부 오류"]);
  });
});
