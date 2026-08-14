import { useEffect, useMemo, useRef, useState } from "react";
import {
  Body1,
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
  mergeClasses,
  tokens,
} from "@fluentui/react-components";
import { PlayRegular } from "@fluentui/react-icons";
import { sampleSchools, ApiError } from "../api/client";
import { streamLunchAnalysis } from "../api/agentClient";
import { bankStylePalette } from "../theme";
import type { LunchBattleResult, School } from "../types";
import { AnalysisResult } from "./AnalysisResult";

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
  cardGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: "12px",
  },
  schoolCard: {
    cursor: "pointer",
    padding: "14px",
    display: "flex",
    flexDirection: "column",
    gap: "6px",
    borderRadius: tokens.borderRadiusXLarge,
    transitionDuration: tokens.durationNormal,
    transitionProperty: "transform, box-shadow, border-color",
    ":hover": {
      transform: "translateY(-1px)",
      boxShadow: tokens.shadow8,
    },
  },
  schoolCardDisabled: {
    cursor: "not-allowed",
    opacity: 0.5,
    ":hover": {
      transform: "none",
      boxShadow: "none",
    },
  },
  schoolCardSelected: {
    outline: `2px solid ${bankStylePalette.gold}`,
    backgroundColor: "#FFF9EA",
  },
  schoolMeta: { color: tokens.colorNeutralForeground3 },
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

function isSelectedSchool(selectedSchools: School[], school: School): boolean {
  return selectedSchools.some(
    (selected) =>
      selected.schoolCode === school.schoolCode &&
      selected.eduOfficeCode === school.eduOfficeCode,
  );
}

function asSelectedPair(selectedSchools: School[]): [School, School] | null {
  return selectedSchools.length === 2
    ? [selectedSchools[0], selectedSchools[1]]
    : null;
}

export function LunchAnalysisPage() {
  const styles = useStyles();
  const today = useMemo(() => new Date(), []);
  const [schools, setSchools] = useState<School[]>([]);
  const [sampleLoading, setSampleLoading] = useState(false);
  const [sampleError, setSampleError] = useState<string | null>(null);
  const [selectedSchools, setSelectedSchools] = useState<School[]>([]);
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
  const requestIdRef = useRef(0);
  const lastAutoPromptRef = useRef("");

  const monthRange = useMemo(
    () => getMonthRange(today, selectedMonth),
    [selectedMonth, today],
  );
  const selectedPair = asSelectedPair(selectedSchools);
  const generatedPrompt =
    selectedPair && selectedDate
      ? buildDefaultPrompt(selectedPair, selectedDate)
      : "";

  async function loadSampleSchools() {
    const requestId = ++requestIdRef.current;
    setSampleLoading(true);
    setSampleError(null);
    try {
      const result = await sampleSchools();
      if (requestId !== requestIdRef.current) {
        return;
      }
      setSchools(result.schools);
    } catch (error) {
      if (requestId !== requestIdRef.current) {
        return;
      }
      setSampleError(
        error instanceof ApiError
          ? error.message
          : "학교 샘플을 불러오는 중 오류가 발생했습니다.",
      );
    } finally {
      if (requestId === requestIdRef.current) {
        setSampleLoading(false);
      }
    }
  }

  useEffect(() => {
    void loadSampleSchools();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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

  function handleToggleSchool(school: School) {
    const alreadySelected = isSelectedSchool(selectedSchools, school);
    const nextSelectedSchools = alreadySelected
      ? selectedSchools.filter(
          (selected) =>
            !(
              selected.schoolCode === school.schoolCode &&
              selected.eduOfficeCode === school.eduOfficeCode
            ),
        )
      : [...selectedSchools, school];

    if (!alreadySelected && selectedSchools.length >= 2) {
      return;
    }

    setSelectedSchools(nextSelectedSchools);
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
    const hasTwoSchools = selectedSchools.length === 2;
    const hasDate = selectedDate.length > 0;
    setSchoolValidationError(hasTwoSchools ? null : "학교를 2개 선택해 주세요.");
    setDateValidationError(hasDate ? null : "분석 날짜를 선택해 주세요.");

    if (!hasTwoSchools || !hasDate) {
      return;
    }

    const selectedPairValue = asSelectedPair(selectedSchools);
    if (!selectedPairValue) {
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
          schoolA: selectedPairValue[0],
          schoolB: selectedPairValue[1],
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

        {sampleLoading && (
          <div role="status" aria-live="polite">
            <Spinner label="분석용 학교 샘플을 불러오는 중..." />
          </div>
        )}

        {sampleError && (
          <MessageBar intent="error">
            <MessageBarBody>{sampleError}</MessageBarBody>
          </MessageBar>
        )}

        {!sampleLoading && !sampleError && (
          <>
            <div className={styles.selectedSummary}>
              <Caption1>
                선택된 학교: {selectedSchools.length} / 2
              </Caption1>
              {selectedSchools.map((school, index) => (
                <span
                  className={styles.selectedChip}
                  key={`${school.eduOfficeCode}-${school.schoolCode}`}
                >
                  {index === 0 ? "A" : "B"} · {school.schoolName}
                </span>
              ))}
            </div>

            <div className={styles.cardGrid} aria-label="분석용 학교 샘플">
              {schools.map((school) => {
                const selected = isSelectedSchool(selectedSchools, school);
                const disabled = !selected && selectedSchools.length >= 2;

                return (
                  <Card
                    key={`${school.eduOfficeCode}-${school.schoolCode}`}
                    className={mergeClasses(
                      styles.schoolCard,
                      selected && styles.schoolCardSelected,
                      disabled && styles.schoolCardDisabled,
                    )}
                    aria-disabled={disabled}
                    aria-pressed={selected}
                    onClick={() => {
                      if (!disabled) {
                        handleToggleSchool(school);
                      }
                    }}
                    onKeyDown={(event) => {
                      if ((event.key === "Enter" || event.key === " ") && !disabled) {
                        event.preventDefault();
                        handleToggleSchool(school);
                      }
                    }}
                    role="button"
                    tabIndex={disabled ? -1 : 0}
                  >
                    <Body1>
                      <strong>{school.schoolName}</strong>
                    </Body1>
                    <Caption1 className={styles.schoolMeta}>
                      {[school.region, school.schoolKind, school.address]
                        .filter(Boolean)
                        .join(" · ")}
                    </Caption1>
                  </Card>
                );
              })}
            </div>

            {schoolValidationError && (
              <MessageBar intent="error">
                <MessageBarBody>{schoolValidationError}</MessageBarBody>
              </MessageBar>
            )}
          </>
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
            disabled={analysisLoading || sampleLoading || schools.length === 0}
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
