import { useEffect, useMemo, useRef, useState } from "react";
import {
  Button,
  Caption1,
  Card,
  Divider,
  Field,
  MessageBar,
  MessageBarBody,
  Radio,
  RadioGroup,
  Spinner,
  Subtitle1,
  Textarea,
  makeStyles,
  tokens,
} from "@fluentui/react-components";
import { PlayRegular } from "@fluentui/react-icons";
import { ApiError } from "../api/client";
import { streamLunchAnalysis } from "../api/agentClient";
import { bankStylePalette } from "../theme";
import type { LunchBattleResult, School } from "../types";
import { AnalysisResult } from "./AnalysisResult";
import { SchoolSearch } from "./SchoolSearch";

type AnalysisMonth = "current" | "previous";

interface MonthRange {
  min: string;
  max: string;
}

const STEP_CARD_GAP = "16px";

const useStyles = makeStyles({
  layout: {
    display: "flex",
    flexDirection: "column",
    gap: STEP_CARD_GAP,
  },
  stepCard: {
    padding: "20px",
    borderRadius: tokens.borderRadiusXLarge,
    boxShadow: "0 2px 10px rgba(27, 42, 74, 0.08)",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  stepHeader: { display: "flex", alignItems: "center", gap: "10px" },
  stepBadge: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    width: "28px",
    height: "28px",
    borderRadius: "50%",
    backgroundColor: bankStylePalette.gold,
    color: bankStylePalette.navy,
    fontWeight: 700,
    fontSize: "14px",
    flexShrink: 0,
  },
  stepTitle: { color: bankStylePalette.navy },
  schoolSearchGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
    gap: "16px",
  },
  schoolSearchColumn: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  schoolSearchLabel: { color: bankStylePalette.navy },
  selectedSummary: {
    display: "flex",
    flexWrap: "wrap",
    gap: "8px",
    alignItems: "center",
  },
  selectedChip: {
    padding: "8px 12px",
    borderRadius: tokens.borderRadiusLarge,
    backgroundColor: "#FFF9EA",
    color: bankStylePalette.navy,
    border: `1px solid ${bankStylePalette.goldSoft}`,
  },
  dateSection: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  monthHint: { color: tokens.colorNeutralForeground3 },
  actions: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
});

function formatDateInput(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatKoreanDate(isoDate: string): string {
  const [yearText, monthText, dayText] = isoDate.split("-");
  const year = Number(yearText);
  const month = Number(monthText);
  const day = Number(dayText);
  if (!year || !month || !day) {
    return isoDate;
  }

  return `${year}년 ${month}월 ${day}일`;
}

function getMonthRange(today: Date, month: AnalysisMonth): MonthRange {
  const rangeMonthDate =
    month === "current"
      ? new Date(today.getFullYear(), today.getMonth(), 1)
      : new Date(today.getFullYear(), today.getMonth() - 1, 1);
  const min = new Date(rangeMonthDate.getFullYear(), rangeMonthDate.getMonth(), 1);
  const max =
    month === "current"
      ? new Date(today.getFullYear(), today.getMonth(), today.getDate())
      : new Date(rangeMonthDate.getFullYear(), rangeMonthDate.getMonth() + 1, 0);

  return {
    min: formatDateInput(min),
    max: formatDateInput(max),
  };
}

function buildDefaultPrompt(
  selectedSchools: [School, School],
  date: string,
): string {
  const [schoolA, schoolB] = selectedSchools;
  return `${schoolA.schoolName}와 ${schoolB.schoolName}의 ${formatKoreanDate(date)} 중식 급식을 EVALUATION_RUBRIC.md 기준(영양 균형, 건강성, 식재료 및 메뉴 품질, 급식 참여도)으로 비교 평가해 주세요.`;
}

function isSameSchool(a: School | null, b: School | null): boolean {
  if (!a || !b) {
    return false;
  }
  return a.schoolCode === b.schoolCode && a.eduOfficeCode === b.eduOfficeCode;
}

function asSelectedPair(
  schoolA: School | null,
  schoolB: School | null,
): [School, School] | null {
  if (!schoolA || !schoolB || isSameSchool(schoolA, schoolB)) {
    return null;
  }
  return [schoolA, schoolB];
}

export function LunchAnalysisPage() {
  const styles = useStyles();
  const today = useMemo(() => new Date(), []);
  const [schoolA, setSchoolA] = useState<School | null>(null);
  const [schoolB, setSchoolB] = useState<School | null>(null);
  const [schoolValidationError, setSchoolValidationError] = useState<string | null>(
    null,
  );
  const [selectedMonth, setSelectedMonth] = useState<AnalysisMonth>("current");
  const [selectedDate, setSelectedDate] = useState("");
  const [dateValidationError, setDateValidationError] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("");
  const [promptTouched, setPromptTouched] = useState(false);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState("");
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<LunchBattleResult | null>(null);
  const lastAutoPromptRef = useRef("");

  const monthRange = useMemo(
    () => getMonthRange(today, selectedMonth),
    [selectedMonth, today],
  );
  const selectedPair = asSelectedPair(schoolA, schoolB);
  const generatedPrompt =
    selectedPair && selectedDate
      ? buildDefaultPrompt(selectedPair, selectedDate)
      : "";

  useEffect(() => {
    if (selectedDate && (selectedDate < monthRange.min || selectedDate > monthRange.max)) {
      setSelectedDate("");
    }
  }, [monthRange.max, monthRange.min, selectedDate]);

  useEffect(() => {
    if (!generatedPrompt) {
      return;
    }

    const previousAutoPrompt = lastAutoPromptRef.current;
    const shouldReplacePrompt =
      prompt === previousAutoPrompt || !promptTouched;
    lastAutoPromptRef.current = generatedPrompt;

    if (shouldReplacePrompt) {
      setPrompt(generatedPrompt);
      setPromptTouched(false);
    }
  }, [generatedPrompt, prompt, promptTouched]);

  function resetAnalysisOutput() {
    setAnalysisError(null);
    setAnalysisProgress("");
    setAnalysisResult(null);
  }

  function handleSelectSchoolA(school: School) {
    if (isSameSchool(school, schoolB)) {
      setSchoolValidationError("학교 A와 B는 서로 다른 학교여야 합니다.");
      return;
    }
    setSchoolA(school);
    setSchoolValidationError(null);
    resetAnalysisOutput();
  }

  function handleSelectSchoolB(school: School) {
    if (isSameSchool(schoolA, school)) {
      setSchoolValidationError("학교 A와 B는 서로 다른 학교여야 합니다.");
      return;
    }
    setSchoolB(school);
    setSchoolValidationError(null);
    resetAnalysisOutput();
  }

  function handleDateChange(value: string) {
    setSelectedDate(value);
    setDateValidationError(null);
    resetAnalysisOutput();
  }

  function handlePromptChange(value: string) {
    setPrompt(value);
    setPromptTouched(value !== lastAutoPromptRef.current);
    setAnalysisError(null);
  }

  async function handleStartAnalysis() {
    const hasTwoSchools = selectedPair !== null;
    const hasDate = selectedDate.length > 0;
    setSchoolValidationError(hasTwoSchools ? null : "서로 다른 학교 2곳을 선택해 주세요.");
    setDateValidationError(hasDate ? null : "분석 날짜를 선택해 주세요.");

    if (!selectedPair || !hasDate) {
      return;
    }

    const trimmedPrompt = prompt.trim();
    if (!trimmedPrompt) {
      setAnalysisError("분석 프롬프트를 입력해 주세요.");
      return;
    }

    setAnalysisLoading(true);
    setAnalysisError(null);
    setAnalysisProgress("");
    setAnalysisResult(null);

    try {
      await streamLunchAnalysis(
        {
          schoolA: selectedPair[0],
          schoolB: selectedPair[1],
          date: selectedDate,
          prompt: trimmedPrompt,
        },
        {
          onProgress: setAnalysisProgress,
          onResult: setAnalysisResult,
          onError: setAnalysisError,
        },
      );
    } catch (error) {
      if (!(error instanceof ApiError)) {
        setAnalysisError("급식 분석 중 오류가 발생했습니다.");
      }
    } finally {
      setAnalysisLoading(false);
    }
  }

  return (
    <div className={styles.layout}>
      <Card className={styles.stepCard}>
        <div className={styles.stepHeader}>
          <span className={styles.stepBadge}>1</span>
          <Subtitle1 className={styles.stepTitle}>
            학교 2곳 선택
          </Subtitle1>
        </div>
        <Divider />

        <div className={styles.selectedSummary}>
          {schoolA && (
            <span className={styles.selectedChip}>A · {schoolA.schoolName}</span>
          )}
          {schoolB && (
            <span className={styles.selectedChip}>B · {schoolB.schoolName}</span>
          )}
        </div>

        <div className={styles.schoolSearchGrid}>
          <div className={styles.schoolSearchColumn}>
            <Caption1 className={styles.schoolSearchLabel}>
              <strong>학교 A</strong>
            </Caption1>
            <SchoolSearch selectedSchool={schoolA} onSelect={handleSelectSchoolA} />
          </div>
          <div className={styles.schoolSearchColumn}>
            <Caption1 className={styles.schoolSearchLabel}>
              <strong>학교 B</strong>
            </Caption1>
            <SchoolSearch selectedSchool={schoolB} onSelect={handleSelectSchoolB} />
          </div>
        </div>

        {schoolValidationError && (
          <MessageBar intent="error">
            <MessageBarBody>{schoolValidationError}</MessageBarBody>
          </MessageBar>
        )}
      </Card>

      <Card className={styles.stepCard}>
        <div className={styles.stepHeader}>
          <span className={styles.stepBadge}>2</span>
          <Subtitle1 className={styles.stepTitle}>
            분석 날짜 선택
          </Subtitle1>
        </div>
        <Divider />

        <div className={styles.dateSection}>
          <RadioGroup
            aria-label="분석 대상 월"
            value={selectedMonth}
            layout="horizontal"
            onChange={(_, data) => {
              setSelectedMonth(data.value as AnalysisMonth);
              setDateValidationError(null);
              resetAnalysisOutput();
            }}
          >
            <Radio label="이번달" value="current" />
            <Radio label="직전달" value="previous" />
          </RadioGroup>

          <Field
            label="분석 날짜"
            validationState={dateValidationError ? "error" : "none"}
            hint={{
              children: (
                <Caption1 className={styles.monthHint}>
                  선택 가능한 범위: {monthRange.min} ~ {monthRange.max}
                </Caption1>
              ),
            }}
          >
            <input
              aria-label="분석 날짜"
              max={monthRange.max}
              min={monthRange.min}
              onChange={(event) => handleDateChange(event.target.value)}
              type="date"
              value={selectedDate}
            />
          </Field>

          {dateValidationError && (
            <MessageBar intent="error">
              <MessageBarBody>{dateValidationError}</MessageBarBody>
            </MessageBar>
          )}
        </div>
      </Card>

      <Card className={styles.stepCard}>
        <div className={styles.stepHeader}>
          <span className={styles.stepBadge}>3</span>
          <Subtitle1 className={styles.stepTitle}>
            분석 프롬프트 확인
          </Subtitle1>
        </div>
        <Divider />

        <div className={styles.actions}>
          <Field
            label="분석 요청문"
            hint={
              generatedPrompt ? (
                <Caption1>
                  자동 생성된 문구를 수정해도 됩니다.
                </Caption1>
              ) : (
                <Caption1>
                  학교 2곳과 날짜를 선택하면 기본 요청문이 자동으로 채워집니다.
                </Caption1>
              )
            }
          >
            <Textarea
              aria-label="분석 요청문"
              placeholder="비교 기준이나 원하는 표현을 추가로 적어 주세요."
              resize="vertical"
              rows={4}
              value={prompt}
              onChange={(_, data) => handlePromptChange(data.value)}
            />
          </Field>

          <Button
            appearance="primary"
            disabled={analysisLoading}
            icon={analysisLoading ? <Spinner size="tiny" /> : <PlayRegular />}
            onClick={() => void handleStartAnalysis()}
          >
            분석 시작
          </Button>

          {analysisError && !analysisLoading && (
            <MessageBar intent="error">
              <MessageBarBody>{analysisError}</MessageBarBody>
            </MessageBar>
          )}
        </div>
      </Card>

      <Card className={styles.stepCard}>
        <div className={styles.stepHeader}>
          <span className={styles.stepBadge}>4</span>
          <Subtitle1 className={styles.stepTitle}>
            분석 결과
          </Subtitle1>
        </div>
        <Divider />
        <AnalysisResult
          error={analysisLoading ? null : analysisError}
          loading={analysisLoading}
          progressText={analysisProgress}
          result={analysisResult}
        />
      </Card>
    </div>
  );
}
