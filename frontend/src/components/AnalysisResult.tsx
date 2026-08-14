import {
  Badge,
  Body1,
  Caption1,
  Card,
  MessageBar,
  MessageBarBody,
  Spinner,
  Subtitle1,
  Title3,
  makeStyles,
  tokens,
} from "@fluentui/react-components";
import { bankStylePalette } from "../theme";
import type {
  LunchAnalysisArea,
  LunchAnalysisAreaKey,
  LunchBattleResult,
} from "../types";

/** 평가 영역 키 → 한국어 표시명 (EVALUATION_RUBRIC.md 순서와 동일). */
const AREA_LABELS: Record<LunchAnalysisAreaKey, string> = {
  nutritionBalance: "영양 균형",
  healthiness: "건강성",
  menuQuality: "식재료 및 메뉴 품질",
  mealParticipation: "급식 참여도",
};

const AREA_ORDER: LunchAnalysisAreaKey[] = [
  "nutritionBalance",
  "healthiness",
  "menuQuality",
  "mealParticipation",
];

const useStyles = makeStyles({
  empty: {
    padding: "24px 16px",
    textAlign: "center",
    color: tokens.colorNeutralForeground3,
  },
  loading: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "8px",
    padding: "24px 16px",
  },
  progressText: {
    color: tokens.colorNeutralForeground3,
    textAlign: "center",
    whiteSpace: "pre-wrap",
  },
  scoreGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: "12px",
  },
  scoreCard: {
    padding: "16px",
    borderRadius: tokens.borderRadiusXLarge,
    border: `1px solid ${bankStylePalette.goldSoft}`,
    backgroundColor: "#FFF9EA",
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  scoreLabel: { color: bankStylePalette.navySoft },
  scoreValue: {
    color: bankStylePalette.navy,
    fontSize: tokens.fontSizeHero800,
    fontWeight: tokens.fontWeightSemibold,
    lineHeight: tokens.lineHeightHero800,
  },
  winnerRow: {
    display: "flex",
    flexWrap: "wrap",
    alignItems: "center",
    gap: "8px",
  },
  summaryCard: {
    padding: "16px",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  areas: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  areaCard: {
    padding: "16px",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  areaColumns: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
    gap: "12px",
  },
  schoolAreaCard: {
    padding: "14px",
    backgroundColor: tokens.colorNeutralBackground2,
    borderRadius: tokens.borderRadiusLarge,
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  noteList: {
    margin: 0,
    paddingLeft: "18px",
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
});

interface AreaPair {
  key: LunchAnalysisAreaKey;
  name: string;
  schoolA: LunchAnalysisArea;
  schoolB: LunchAnalysisArea;
}

interface AnalysisResultProps {
  loading: boolean;
  progressText: string;
  error: string | null;
  result: LunchBattleResult | null;
}

function formatScore(score: number): string {
  return Number.isInteger(score) ? `${score}` : score.toFixed(1);
}

function getWinnerLabel(result: LunchBattleResult): string {
  if (result.winner === "tie") {
    return "동점";
  }

  return result.winner === "A"
    ? `${result.schoolA.schoolName} 우세`
    : `${result.schoolB.schoolName} 우세`;
}

function buildAreaPairs(result: LunchBattleResult): AreaPair[] {
  return AREA_ORDER.map((key) => ({
    key,
    name: AREA_LABELS[key],
    schoolA: result.schoolA.areas[key],
    schoolB: result.schoolB.areas[key],
  }));
}

function AreaDetails(props: { schoolName: string; area: LunchAnalysisArea }) {
  const styles = useStyles();

  return (
    <Card className={styles.schoolAreaCard}>
      <Subtitle1>{props.schoolName}</Subtitle1>
      <Body1>점수: {formatScore(props.area.score)} / 5</Body1>
      <Body1>가중 점수: {formatScore(props.area.weightedScore)} / 100</Body1>
      <Caption1>{props.area.rationale}</Caption1>
    </Card>
  );
}

export function AnalysisResult({
  loading,
  progressText,
  error,
  result,
}: AnalysisResultProps) {
  const styles = useStyles();

  if (loading) {
    return (
      <div className={styles.loading} role="status" aria-live="polite">
        <Spinner label="급식 분석을 진행하는 중..." />
        {progressText && (
          <Caption1 className={styles.progressText}>
            진행 상황: {progressText}
          </Caption1>
        )}
      </div>
    );
  }

  if (error) {
    return (
      <MessageBar intent="error">
        <MessageBarBody>{error}</MessageBarBody>
      </MessageBar>
    );
  }

  if (result === null) {
    return (
      <div className={styles.empty}>
        <Body1>
          학교 2곳과 날짜를 선택한 뒤 분석을 시작하면 비교 결과가 이곳에 표시됩니다.
        </Body1>
      </div>
    );
  }

  const areaPairs = buildAreaPairs(result);

  return (
    <section aria-label="급식 분석 결과">
      <div className={styles.scoreGrid}>
        <Card className={styles.scoreCard}>
          <Caption1 className={styles.scoreLabel}>
            {result.schoolA.schoolName}
          </Caption1>
          <div className={styles.scoreValue}>
            {formatScore(result.schoolA.totalScore)}
          </div>
          <Body1>총점 / 100점</Body1>
        </Card>
        <Card className={styles.scoreCard}>
          <Caption1 className={styles.scoreLabel}>
            {result.schoolB.schoolName}
          </Caption1>
          <div className={styles.scoreValue}>
            {formatScore(result.schoolB.totalScore)}
          </div>
          <Body1>총점 / 100점</Body1>
        </Card>
      </div>

      <div className={styles.winnerRow} style={{ marginTop: 16 }}>
        <Subtitle1>최종 판정</Subtitle1>
        <Badge appearance="filled" color="important">
          {getWinnerLabel(result)}
        </Badge>
      </div>

      <Card className={styles.summaryCard} style={{ marginTop: 16 }}>
        <Title3 as="h3">총평</Title3>
        <Body1>{result.summary}</Body1>
      </Card>

      <div className={styles.areas} style={{ marginTop: 16 }}>
        {areaPairs.map((areaPair) => (
          <Card className={styles.areaCard} key={areaPair.key}>
            <Title3 as="h3">{areaPair.name}</Title3>
            <div className={styles.areaColumns}>
              <AreaDetails
                schoolName={result.schoolA.schoolName}
                area={areaPair.schoolA}
              />
              <AreaDetails
                schoolName={result.schoolB.schoolName}
                area={areaPair.schoolB}
              />
            </div>
          </Card>
        ))}
      </div>

      {result.qualityNotes.length > 0 && (
        <Card className={styles.summaryCard} style={{ marginTop: 16 }}>
          <Title3 as="h3">해석 시 참고할 점</Title3>
          <ul className={styles.noteList}>
            {result.qualityNotes.map((note) => (
              <li key={note}>
                <Body1>{note}</Body1>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </section>
  );
}
