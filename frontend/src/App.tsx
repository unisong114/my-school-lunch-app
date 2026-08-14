import { useState } from "react";
import {
  Divider,
  Subtitle1,
  Title1,
  makeStyles,
  tokens,
} from "@fluentui/react-components";
import { SchoolSearch } from "./components/SchoolSearch";
import { DateRangePicker } from "./components/DateRangePicker";
import { MealResults } from "./components/MealResults";
import { ApiError, fetchMeals } from "./api/client";
import type { DailyMeal, School } from "./types";

const useStyles = makeStyles({
  page: {
    maxWidth: "880px",
    margin: "0 auto",
    padding: "24px 16px 64px",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  header: { marginBottom: "8px" },
  subtitle: { color: tokens.colorNeutralForeground3 },
  step: {
    marginTop: "20px",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  stepLabel: { color: tokens.colorBrandForeground1 },
});

/** 시작일이 종료일보다 이후인지 검증합니다. */
function validateRange(from: string, to: string): string | null {
  if (!from || !to) {
    return "시작일과 종료일을 모두 선택해 주세요.";
  }
  if (from > to) {
    return "시작일은 종료일보다 이후일 수 없습니다.";
  }
  return null;
}

export function App() {
  const styles = useStyles();
  const [school, setSchool] = useState<School | null>(null);
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const [meals, setMeals] = useState<DailyMeal[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [mealError, setMealError] = useState<string | null>(null);

  function handleSelectSchool(next: School) {
    setSchool(next);
    setMeals(null);
    setMealError(null);
  }

  async function handleQuery() {
    if (!school) {
      return;
    }
    const error = validateRange(fromDate, toDate);
    setValidationError(error);
    if (error) {
      return;
    }

    setLoading(true);
    setMealError(null);
    setMeals(null);
    try {
      const result = await fetchMeals({
        eduOfficeCode: school.eduOfficeCode,
        schoolCode: school.schoolCode,
        fromDate,
        toDate,
      });
      setMeals(result.meals);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "급식 조회 중 오류가 발생했습니다.";
      setMealError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <Title1 as="h1">🍱 급식 배틀</Title1>
        <Subtitle1 className={styles.subtitle} as="p">
          학교를 검색하고 날짜 범위를 선택하면 중식 급식을 보여드립니다.
        </Subtitle1>
      </header>

      <Divider />

      <div className={styles.step}>
        <Subtitle1 className={styles.stepLabel}>1. 학교 검색 및 선택</Subtitle1>
        <SchoolSearch selectedSchool={school} onSelect={handleSelectSchool} />
      </div>

      {school && (
        <div className={styles.step}>
          <Subtitle1 className={styles.stepLabel}>
            2. 날짜 범위 선택 ({school.schoolName})
          </Subtitle1>
          <DateRangePicker
            fromDate={fromDate}
            toDate={toDate}
            onFromChange={(value) => {
              setFromDate(value);
              setValidationError(null);
            }}
            onToChange={(value) => {
              setToDate(value);
              setValidationError(null);
            }}
            onSubmit={handleQuery}
            disabled={!school}
            loading={loading}
            validationError={validationError}
          />
        </div>
      )}

      {school && (
        <div className={styles.step}>
          <Subtitle1 className={styles.stepLabel}>3. 급식 결과</Subtitle1>
          <MealResults
            meals={meals}
            loading={loading}
            error={mealError}
            schoolName={school.schoolName}
          />
        </div>
      )}
    </main>
  );
}
