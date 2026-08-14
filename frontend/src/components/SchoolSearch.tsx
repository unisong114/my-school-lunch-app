import { useState, type FormEvent } from "react";
import {
  Body1,
  Button,
  Caption1,
  Card,
  Field,
  Input,
  MessageBar,
  MessageBarBody,
  Spinner,
  Text,
  makeStyles,
  mergeClasses,
  tokens,
} from "@fluentui/react-components";
import { SearchRegular } from "@fluentui/react-icons";
import { searchSchools, ApiError } from "../api/client";
import type { School } from "../types";

const useStyles = makeStyles({
  form: { display: "flex", gap: "8px", alignItems: "flex-end" },
  field: { flex: 1 },
  list: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    marginTop: "12px",
  },
  schoolCard: {
    cursor: "pointer",
    padding: "12px",
    ":hover": { backgroundColor: tokens.colorNeutralBackground1Hover },
  },
  selected: {
    outline: `2px solid ${tokens.colorBrandStroke1}`,
  },
  meta: { color: tokens.colorNeutralForeground3 },
});

interface SchoolSearchProps {
  selectedSchool: School | null;
  onSelect: (school: School) => void;
}

export function SchoolSearch({ selectedSchool, onSelect }: SchoolSearchProps) {
  const styles = useStyles();
  const [query, setQuery] = useState("");
  const [schools, setSchools] = useState<School[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const name = query.trim();
    if (!name) {
      setError("학교 이름을 입력해 주세요.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await searchSchools(name);
      setSchools(result.schools);
      setSearched(true);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "학교 검색 중 오류가 발생했습니다.";
      setError(message);
      setSchools([]);
      setSearched(true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section aria-label="학교 검색">
      <form className={styles.form} onSubmit={handleSubmit} role="search">
        <Field className={styles.field} label="학교 이름">
          <Input
            aria-label="학교 이름 검색"
            placeholder="예: 서울고, 한밭초"
            value={query}
            contentBefore={<SearchRegular />}
            onChange={(_, data) => setQuery(data.value)}
          />
        </Field>
        <Button
          type="submit"
          appearance="primary"
          disabled={loading}
          icon={loading ? <Spinner size="tiny" /> : <SearchRegular />}
        >
          검색
        </Button>
      </form>

      {error && (
        <MessageBar intent="error" style={{ marginTop: 12 }}>
          <MessageBarBody>{error}</MessageBarBody>
        </MessageBar>
      )}

      {!error && searched && !loading && schools.length === 0 && (
        <MessageBar intent="warning" style={{ marginTop: 12 }}>
          <MessageBarBody>
            검색 결과가 없습니다. 다른 학교 이름으로 검색해 보세요.
          </MessageBarBody>
        </MessageBar>
      )}

      {schools.length > 0 && (
        <ul
          className={styles.list}
          aria-label="학교 검색 결과"
          style={{ listStyle: "none", padding: 0, margin: "12px 0 0" }}
        >
          {schools.map((school) => {
            const isSelected =
              selectedSchool?.schoolCode === school.schoolCode &&
              selectedSchool?.eduOfficeCode === school.eduOfficeCode;
            return (
              <li key={`${school.eduOfficeCode}-${school.schoolCode}`}>
                <Card
                  className={mergeClasses(
                    styles.schoolCard,
                    isSelected && styles.selected,
                  )}
                  onClick={() => onSelect(school)}
                  aria-pressed={isSelected}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      onSelect(school);
                    }
                  }}
                >
                  <Body1>
                    <strong>{school.schoolName}</strong>
                  </Body1>
                  <Caption1 className={styles.meta}>
                    {[school.region, school.schoolKind, school.address]
                      .filter(Boolean)
                      .join(" · ")}
                  </Caption1>
                  {isSelected && (
                    <Text size={200} weight="semibold">
                      선택됨
                    </Text>
                  )}
                </Card>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
