# E2E 테스트 (Playwright)

학교 검색 → 날짜 선택 → 급식 결과 표시의 전체 사용자 흐름을 브라우저에서 검증합니다.
백엔드 API는 네트워크 경계에서 스텁 처리하여 NEIS 실데이터에 의존하지 않고
안정적으로 실행됩니다.

## 실행

```bash
# 프론트엔드 빌드가 선행되어야 합니다.
npm --prefix ../frontend run build

npm install
npx playwright install chromium
npm test
```

기본적으로 `../frontend` 의 preview 서버(`http://localhost:4173`)를 자동 기동합니다.
이미 실행 중인 프론트엔드를 대상으로 하려면 `E2E_BASE_URL` 환경 변수를 지정하세요.

## 검증 시나리오 (`tests/flow.spec.ts`)

- 학교 검색 → 날짜 선택 → 중식 급식 결과 표시
- 검색 결과 없음 안내
- 잘못된 날짜 범위 차단
- 급식 정보 없음 안내
