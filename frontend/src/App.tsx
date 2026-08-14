import { useState } from "react";
import {
  Body1,
  Card,
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
import { bankStylePalette } from "./theme";
import type { DailyMeal, School } from "./types";

const useStyles = makeStyles({
  page: {
    minHeight: "100vh",
    backgroundColor: "#F3F4F7",
  },
  hero: {
    background: `linear-gradient(135deg, ${bankStylePalette.gold} 0%, #FFCF52 100%)`,
    borderBottomLeftRadius: "28px",
    borderBottomRightRadius: "28px",
    padding: "40px 24px 56px",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    textAlign: "center",
    gap: "6px",
    boxShadow: "0 4px 16px rgba(27, 42, 74, 0.15)",
  },
  heroTitle: { color: bankStylePalette.navy },
  heroSubtitle: { color: bankStylePalette.navySoft },
  content: {
    maxWidth: "880px",
    margin: "-32px auto 0",
    padding: "0 16px 64px",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
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
    <div className={styles.page}>
      <header className={styles.hero}>
        <Title1 as="h1" className={styles.heroTitle}>
          🍱 급식 배틀
        </Title1>
        <Body1 as="p" className={styles.heroSubtitle}>
          학교를 검색하고 날짜 범위를 선택하면 중식 급식을 보여드립니다.
        </Body1>
      </header>

      <main className={styles.content}>
        <Card className={styles.stepCard}>
          <div className={styles.stepHeader}>
            <span className={styles.stepBadge}>1</span>
            <Subtitle1 className={styles.stepTitle}>
              학교 검색 및 선택
            </Subtitle1>
          </div>
          <Divider />
          <SchoolSearch selectedSchool={school} onSelect={handleSelectSchool} />
        </Card>

        {school && (
          <Card className={styles.stepCard}>
            <div className={styles.stepHeader}>
              <span className={styles.stepBadge}>2</span>
              <Subtitle1 className={styles.stepTitle}>
                날짜 범위 선택 ({school.schoolName})
              </Subtitle1>
            </div>
            <Divider />
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
          </Card>
        )}

        {school && (
          <Card className={styles.stepCard}>
            <div className={styles.stepHeader}>
              <span className={styles.stepBadge}>3</span>
              <Subtitle1 className={styles.stepTitle}>급식 결과</Subtitle1>
            </div>
            <Divider />
            <MealResults
              meals={meals}
              loading={loading}
              error={mealError}
              schoolName={school.schoolName}
            />
          </Card>
        )}
      </main>
    </div>
  );
}
