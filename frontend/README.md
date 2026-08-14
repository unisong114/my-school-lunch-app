# 프론트엔드 (React + Fluent UI)

PRD의 3단계 사용자 흐름(학교 검색 → 날짜 선택 → 중식 급식 결과 표시)을 구현한
React SPA 입니다. Vite 로 빌드하며 Fluent UI(Fluent Design)로 화면을 구성합니다.
백엔드 API만 호출하며 NEIS API를 직접 호출하지 않습니다.

## 로컬 개발

```bash
npm install
npm run dev   # http://localhost:5173 (/api 요청은 http://localhost:8000 로 프록시)
```

백엔드 주소를 바꾸려면 `VITE_BACKEND_URL` 환경 변수를 사용합니다.

## 빌드

```bash
npm run build     # 타입 검사 후 dist/ 생성
npm run preview   # 빌드 결과 미리보기 (http://localhost:4173)
```

## 테스트

```bash
npm test   # Vitest + Testing Library + MSW 통합 테스트
```

통합 테스트는 `tests/integration.test.tsx` 에서 학교 검색 → 날짜 선택 → 결과 표시
흐름과 예외 상황(검색 결과 없음, 잘못된 날짜 범위, 급식 없음, API 오류)을 검증합니다.

## 주요 구성

| 경로 | 설명 |
|------|------|
| `src/api/client.ts` | 백엔드 API 클라이언트 (유일한 통신 경로) |
| `src/components/SchoolSearch.tsx` | 학교 검색·선택 |
| `src/components/DateRangePicker.tsx` | 날짜 범위 선택·검증 |
| `src/components/MealResults.tsx` | 날짜별 중식 급식 표시 |
| `src/App.tsx` | 3단계 흐름 오케스트레이션 |
