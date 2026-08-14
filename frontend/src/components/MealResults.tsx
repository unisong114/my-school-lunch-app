import {
  Badge,
  Body1,
  Caption1,
  Card,
  CardHeader,
  MessageBar,
  MessageBarBody,
  Spinner,
  Text,
  makeStyles,
  tokens,
} from "@fluentui/react-components";
import type { DailyMeal } from "../types";

const useStyles = makeStyles({
  list: {
    display: "grid",
    gap: "12px",
    gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
    marginTop: "12px",
  },
  dishes: { display: "flex", flexDirection: "column", gap: "4px", marginTop: "8px" },
  dishRow: { display: "flex", gap: "6px", alignItems: "center" },
  meta: { color: tokens.colorNeutralForeground3, marginTop: "8px" },
  center: { display: "flex", justifyContent: "center", padding: "24px" },
});

function formatDate(iso: string): string {
  const parsed = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) {
    return iso;
  }
  const weekday = ["일", "월", "화", "수", "목", "금", "토"][parsed.getDay()];
  return `${iso} (${weekday})`;
}

interface MealResultsProps {
  meals: DailyMeal[] | null;
  loading: boolean;
  error: string | null;
  schoolName?: string;
}

export function MealResults({
  meals,
  loading,
  error,
  schoolName,
}: MealResultsProps) {
  const styles = useStyles();

  if (loading) {
    return (
      <div className={styles.center} role="status" aria-live="polite">
        <Spinner label="급식 정보를 불러오는 중..." />
      </div>
    );
  }

  if (error) {
    return (
      <MessageBar intent="error" style={{ marginTop: 12 }}>
        <MessageBarBody>{error}</MessageBarBody>
      </MessageBar>
    );
  }

  if (meals === null) {
    return null;
  }

  if (meals.length === 0) {
    return (
      <MessageBar intent="info" style={{ marginTop: 12 }}>
        <MessageBarBody>
          선택한 기간에 급식 정보가 없습니다. 주말·공휴일·방학 기간에는 급식이
          제공되지 않을 수 있습니다.
        </MessageBarBody>
      </MessageBar>
    );
  }

  return (
    <section aria-label="급식 조회 결과">
      {schoolName && (
        <Text size={400} weight="semibold">
          {schoolName} 중식 급식
        </Text>
      )}
      <ul
        className={styles.list}
        aria-label="날짜별 급식"
        style={{ listStyle: "none", padding: 0, margin: 0 }}
      >
        {meals.map((meal) => (
          <li key={meal.date}>
            <Card>
              <CardHeader
                header={<Body1><strong>{formatDate(meal.date)}</strong></Body1>}
                description={<Caption1>{meal.mealName}</Caption1>}
              />
              <div className={styles.dishes}>
                {meal.dishes.map((dish, index) => (
                  <div className={styles.dishRow} key={`${meal.date}-${index}`}>
                    <Text>{dish.name}</Text>
                    {dish.allergies.length > 0 && (
                      <Badge
                        appearance="tint"
                        color="warning"
                        size="small"
                        aria-label={`알레르기 유발 번호 ${dish.allergies.join(", ")}`}
                      >
                        {dish.allergies.join(".")}
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
              {meal.calorie && (
                <Caption1 className={styles.meta}>열량: {meal.calorie}</Caption1>
              )}
            </Card>
          </li>
        ))}
      </ul>
    </section>
  );
}
