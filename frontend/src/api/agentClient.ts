import { ApiError } from "./client";
import type {
  LunchAnalysisArea,
  LunchAnalysisAreaKey,
  LunchAnalysisRequest,
  LunchAnalysisRequestState,
  LunchBattleResult,
  LunchBattleSchoolResult,
  School,
} from "../types";

const AGENT_API_BASE = import.meta.env.VITE_AGENT_API_BASE ?? "http://localhost:9100";

interface StreamLunchAnalysisArgs {
  schoolA: School;
  schoolB: School;
  date: string;
  prompt: string;
  threadId?: string;
  runId?: string;
}

interface StreamLunchAnalysisCallbacks {
  onProgress: (text: string) => void;
  onResult: (result: LunchBattleResult) => void;
  onError: (message: string) => void;
}

interface AgentEventBase {
  type: string;
  message?: unknown;
  delta?: unknown;
  value?: unknown;
  snapshot?: unknown;
}

function generateIdentifier(prefix: string): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }

  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function toRequestStateSchool(school: School): LunchAnalysisRequestState["schoolA"] {
  return {
    eduOfficeCode: school.eduOfficeCode,
    schoolCode: school.schoolCode,
    schoolName: school.schoolName,
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

const LUNCH_ANALYSIS_AREA_KEYS = [
  "nutritionBalance",
  "healthiness",
  "menuQuality",
  "mealParticipation",
] as const;

function parseArea(value: unknown): LunchAnalysisArea | null {
  if (!isRecord(value)) {
    return null;
  }

  const { score, weightedScore, rationale } = value;
  if (
    typeof score !== "number" ||
    typeof weightedScore !== "number" ||
    typeof rationale !== "string"
  ) {
    return null;
  }

  return { score, weightedScore, rationale };
}

function parseAreas(
  value: unknown,
): Record<LunchAnalysisAreaKey, LunchAnalysisArea> | null {
  if (!isRecord(value)) {
    return null;
  }

  const areas = {} as Record<LunchAnalysisAreaKey, LunchAnalysisArea>;
  for (const key of LUNCH_ANALYSIS_AREA_KEYS) {
    const parsedArea = parseArea(value[key]);
    if (parsedArea === null) {
      return null;
    }
    areas[key] = parsedArea;
  }

  return areas;
}

function parseSchoolResult(value: unknown): LunchBattleSchoolResult | null {
  if (!isRecord(value)) {
    return null;
  }

  const { eduOfficeCode, schoolCode, schoolName, totalScore, areas } = value;
  if (
    typeof eduOfficeCode !== "string" ||
    typeof schoolCode !== "string" ||
    typeof schoolName !== "string" ||
    typeof totalScore !== "number"
  ) {
    return null;
  }

  const parsedAreas = parseAreas(areas);
  if (parsedAreas === null) {
    return null;
  }

  return {
    eduOfficeCode,
    schoolCode,
    schoolName,
    totalScore,
    areas: parsedAreas,
  };
}

function parseLunchBattleResult(value: unknown): LunchBattleResult | null {
  if (!isRecord(value)) {
    return null;
  }

  const { schoolA, schoolB, winner, summary, qualityNotes } = value;
  const parsedSchoolA = parseSchoolResult(schoolA);
  const parsedSchoolB = parseSchoolResult(schoolB);
  if (
    parsedSchoolA === null ||
    parsedSchoolB === null ||
    (winner !== "A" && winner !== "B" && winner !== "tie") ||
    typeof summary !== "string" ||
    !isStringArray(qualityNotes)
  ) {
    return null;
  }

  return {
    schoolA: parsedSchoolA,
    schoolB: parsedSchoolB,
    winner,
    summary,
    qualityNotes,
  };
}

function extractLunchBattleResult(event: AgentEventBase): LunchBattleResult | null {
  if (event.type === "CUSTOM") {
    return parseLunchBattleResult(event.value);
  }

  if (event.type === "STATE_SNAPSHOT") {
    return parseLunchBattleResult(event.snapshot);
  }

  return null;
}

function parseSseEvent(rawChunk: string): AgentEventBase | null {
  const lines = rawChunk
    .replace(/\r/g, "")
    .split("\n")
    .map((line) => line.trimEnd());
  const dataLines = lines
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trimStart());

  if (dataLines.length === 0) {
    return null;
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(dataLines.join("\n"));
  } catch {
    throw new ApiError("분석 스트림 응답을 해석하지 못했습니다.", 502);
  }

  if (!isRecord(parsed) || typeof parsed.type !== "string") {
    throw new ApiError("분석 스트림 응답 형식이 올바르지 않습니다.", 502);
  }

  return {
    type: parsed.type,
    message: parsed.message,
    delta: parsed.delta,
    value: parsed.value,
    snapshot: parsed.snapshot,
  };
}

async function parseErrorResponse(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string; message?: string };
    if (typeof body.detail === "string" && body.detail) {
      return body.detail;
    }
    if (typeof body.message === "string" && body.message) {
      return body.message;
    }
  } catch {
    try {
      const text = await response.text();
      if (text.trim()) {
        return text.trim();
      }
    } catch {
      // 무시하고 기본 메시지를 사용합니다.
    }
  }

  return "분석 요청을 처리하지 못했습니다.";
}

export async function streamLunchAnalysis(
  args: StreamLunchAnalysisArgs,
  callbacks: StreamLunchAnalysisCallbacks,
): Promise<void> {
  const threadId = args.threadId ?? generateIdentifier("thread");
  const runId = args.runId ?? generateIdentifier("run");
  const requestBody: LunchAnalysisRequest = {
    thread_id: threadId,
    run_id: runId,
    messages: [{ role: "user", content: args.prompt }],
    state: {
      schoolA: toRequestStateSchool(args.schoolA),
      schoolB: toRequestStateSchool(args.schoolB),
      date: args.date,
      prompt: args.prompt,
    },
  };

  let errorNotified = false;

  try {
    let response: Response;
    try {
      response = await fetch(`${AGENT_API_BASE}/agui`, {
        method: "POST",
        headers: {
          Accept: "text/event-stream",
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });
    } catch {
      throw new ApiError(
        "분석 서버에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.",
        0,
      );
    }

    if (!response.ok) {
      throw new ApiError(await parseErrorResponse(response), response.status);
    }

    if (!response.body) {
      throw new ApiError("분석 스트림 응답 본문이 비어 있습니다.", 502);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let progressText = "";
    let finalResult: LunchBattleResult | null = null;
    let finished = false;

    while (!finished) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });
      buffer = buffer.replace(/\r\n/g, "\n");

      let separatorIndex = buffer.indexOf("\n\n");
      while (separatorIndex >= 0) {
        const rawEvent = buffer.slice(0, separatorIndex);
        buffer = buffer.slice(separatorIndex + 2);
        separatorIndex = buffer.indexOf("\n\n");

        if (!rawEvent.trim()) {
          continue;
        }

        const event = parseSseEvent(rawEvent);
        if (!event) {
          continue;
        }

        if (event.type === "TEXT_MESSAGE_CONTENT" && typeof event.delta === "string") {
          progressText += event.delta;
          callbacks.onProgress(progressText);
          continue;
        }

        const parsedResult = extractLunchBattleResult(event);
        if (parsedResult) {
          finalResult = parsedResult;
          callbacks.onResult(parsedResult);
          continue;
        }

        if (event.type === "RUN_ERROR") {
          const message =
            typeof event.message === "string"
              ? event.message
              : "급식 분석 중 오류가 발생했습니다.";
          errorNotified = true;
          callbacks.onError(message);
          throw new ApiError(message, 502);
        }

        if (event.type === "RUN_FINISHED") {
          finished = true;
          await reader.cancel();
          break;
        }
      }

      if (done) {
        break;
      }
    }

    if (!finalResult) {
      throw new ApiError("분석 결과를 받지 못했습니다.", 502);
    }
  } catch (error) {
    if (error instanceof ApiError) {
      if (!errorNotified) {
        callbacks.onError(error.message);
      }
      throw error;
    }

    const fallbackError = new ApiError("급식 분석 중 오류가 발생했습니다.", 502);
    callbacks.onError(fallbackError.message);
    throw fallbackError;
  }
}
