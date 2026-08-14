import { useEffect, useRef, useState, type FormEvent } from "react";
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
  makeStyles,
  mergeClasses,
  tokens,
} from "@fluentui/react-components";
import { SearchRegular } from "@fluentui/react-icons";
import { searchSchools, ApiError } from "../api/client";
import type { School } from "../types";

// 자동완성 debounce 지연(ms) 및 최소 입력 글자 수.
const AUTO_SEARCH_DELAY_MS = 300;
const MIN_QUERY_LENGTH = 1;

const useStyles = makeStyles({
  form: { display: "flex", gap: "8px", alignItems: "flex-end" },
  field: { flex: 1 },
  list: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    marginTop: "12px",
    maxHeight: "360px",
    overflowY: "auto",
  },
  selectedSummary: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "12px",
    marginTop: "12px",
    padding: "12px",
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

  // 최신 요청만 반영하기 위한 순번 (오래된 응답이 늦게 도착해도 무시).
  const requestIdRef = useRef(0);
  // 대기 중인 자동완성 debounce 타이머 (명시적 제출 시 취소하기 위해 보관).
  const debounceTimerRef = useRef<number | null>(null);
  // 학교 선택 직후 query를 학교 이름으로 세팅할 때, 자동완성 검색이 다시
  // 트리거되지 않도록 다음 effect 실행을 한 번 건너뛰기 위한 플래그.
  const justSelectedRef = useRef(false);

  function clearPendingAutoSearch() {
    if (debounceTimerRef.current !== null) {
      window.clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }
  }

  async function runSearch(name: string) {
    const requestId = ++requestIdRef.current;
    setLoading(true);
    setError(null);
    try {
      const result = await searchSchools(name);
      if (requestId !== requestIdRef.current) return; // 최신 요청이 아니면 무시
      setSchools(result.schools);
      setSearched(true);
    } catch (err) {
      if (requestId !== requestIdRef.current) return;
      const message =
        err instanceof ApiError
          ? err.message
          : "학교 검색 중 오류가 발생했습니다.";
      setError(message);
      setSchools([]);
      setSearched(true);
    } finally {
      if (requestId === requestIdRef.current) setLoading(false);
    }
  }

  // 입력 중 일부 키워드만으로도 자동완성처럼 검색 결과를 표시합니다 (debounce 적용).
  useEffect(() => {
    clearPendingAutoSearch();
    if (justSelectedRef.current) {
      // 학교 선택 직후 query가 채워진 것이므로 재검색하지 않습니다.
      justSelectedRef.current = false;
      return;
    }
    const name = query.trim();
    if (name.length < MIN_QUERY_LENGTH) {
      requestIdRef.current += 1; // 진행 중이던 요청 결과를 무효화
      setSchools([]);
      setSearched(false);
      setError(null);
      return;
    }
    debounceTimerRef.current = window.setTimeout(() => {
      debounceTimerRef.current = null;
      void runSearch(name);
    }, AUTO_SEARCH_DELAY_MS);
    return clearPendingAutoSearch;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query]);

  function handleSelect(school: School) {
    clearPendingAutoSearch();
    justSelectedRef.current = true;
    setQuery(school.schoolName);
    setSchools([]);
    setSearched(false);
    setError(null);
    onSelect(school);
  }

  function handleChangeSchool() {
    justSelectedRef.current = true;
    setQuery("");
    setSchools([]);
    setSearched(false);
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    clearPendingAutoSearch();
    const name = query.trim();
    if (!name) {
      setError("학교 이름을 입력해 주세요.");
      return;
    }
    await runSearch(name);
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

      {!error && selectedSchool && schools.length === 0 && (
        <Card className={styles.selectedSummary}>
          <div>
            <Body1>
              <strong>{selectedSchool.schoolName}</strong>
            </Body1>
            <Caption1 className={styles.meta}>
              {[
                selectedSchool.region,
                selectedSchool.schoolKind,
                selectedSchool.address,
              ]
                .filter(Boolean)
                .join(" · ")}
            </Caption1>
          </div>
          <Button appearance="secondary" onClick={handleChangeSchool}>
            변경
          </Button>
        </Card>
      )}

      {!error && !selectedSchool && searched && !loading && schools.length === 0 && (
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
                  onClick={() => handleSelect(school)}
                  aria-pressed={isSelected}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      handleSelect(school);
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
                </Card>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
