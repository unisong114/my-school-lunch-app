# 백엔드 (FastAPI)

NEIS 공개 API를 중계·가공해 학교 검색과 중식 급식 조회를 제공하는 API 서버입니다.
프론트엔드는 이 백엔드만 호출하며 NEIS API를 직접 호출하지 않습니다.

## 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/health` | 헬스 체크 |
| GET | `/api/schools?name=서울` | 부분 학교명 검색 |
| GET | `/api/meals?eduOfficeCode=&schoolCode=&fromDate=&toDate=` | 중식 급식 조회 (YYYY-MM-DD) |

내부 API 계약은 [`../src/openapi.json`](../src/openapi.json) 을 참고하세요.

## 로컬 개발

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate  /  Unix: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# NEIS_API_KEY 를 환경 변수로 설정 (미설정 시 인증 없이 동작하나 호출량 제한 가능)
uvicorn app.main:app --reload
```

- API 문서(Swagger): http://localhost:8000/docs

## 테스트

```bash
pytest
```

- 단위 테스트: `tests/test_neis_client.py`, `tests/test_services.py`
- 통합 테스트: `tests/test_routes.py`

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `NEIS_API_KEY` | (없음) | NEIS 공개 API 인증 키 |
| `NEIS_BASE_URL` | `https://open.neis.go.kr/hub` | NEIS API 기본 URL |
| `NEIS_TIMEOUT_SECONDS` | `10` | 호출 타임아웃(초) |
| `CORS_ALLOW_ORIGINS` | `*` | 쉼표 구분 허용 Origin |
