# 급식 배틀 MCP 서버

NEIS 공개 API(`data/openapi.json`)를 활용해 학교 검색과 중식 기준 급식 조회
기능을 MCP(Model Context Protocol) 도구로 제공하는 Python 서버입니다. 기존
백엔드 API 앱(`backend/`)과는 독립적으로 실행되며, NEIS API를 직접 호출합니다.

- **전송 방식**: Streamable HTTP (공식 MCP Python SDK `mcp` 1.x, `FastMCP`)
- **기본 엔드포인트**: `http://<host>:<port>/mcp` (기본 포트 `8100`)
- **제공 도구**
  - `search_schools(school_name)`: 부분 학교명으로 후보 학교의 이름·교육청 정보·학교 식별 정보 조회
  - `get_meals(edu_office_code, school_code, from_date, to_date)`: 선택한 학교와 날짜 범위로 중식 기준 날짜별 급식 조회

## 환경 변수

| 변수                    | 기본값                             | 설명                              |
|-------------------------|-------------------------------------|-----------------------------------|
| `NEIS_API_KEY`          | (빈 값)                             | NEIS 공개 API 인증 키             |
| `NEIS_BASE_URL`         | `https://open.neis.go.kr/hub`       | NEIS API 기본 URL                 |
| `NEIS_TIMEOUT_SECONDS`  | `10.0`                              | NEIS API 호출 타임아웃(초)        |
| `MCP_HOST`              | `0.0.0.0`                           | MCP 서버 바인딩 호스트            |
| `MCP_PORT`              | `8100`                              | MCP 서버 바인딩 포트              |

`.env` 파일을 이 디렉터리(`src/mcp/`)에 두면 자동으로 로드됩니다.

## 로컬 실행

```bash
cd src/mcp
pip install -r requirements.txt
python -m app.main
```

서버가 시작되면 `http://localhost:8100/mcp` 로 MCP 클라이언트가 연결할 수 있습니다.

## MCP Inspector로 확인하기

[MCP Inspector](https://github.com/modelcontextprotocol/inspector)는 Node.js
기반 도구로, Python/Docker 설치 없이도 Node.js만 있으면 실행할 수 있습니다.

1. 위 "로컬 실행" 단계로 MCP 서버를 먼저 실행합니다.
2. 별도 터미널에서 Inspector를 실행합니다.

   ```bash
   npx -y @modelcontextprotocol/inspector
   ```

3. 브라우저에 열리는 Inspector UI에서 다음과 같이 연결합니다.
   - Transport Type: `Streamable HTTP`
   - URL: `http://localhost:8100/mcp`
4. "Connect" 후 "List Tools"로 `search_schools`, `get_meals` 도구를 확인하고,
   각 도구를 호출해 응답(또는 오류 응답)을 검증합니다.

## Docker Compose로 실행하기

저장소 루트에서 다음을 실행하면 프론트엔드·백엔드와 함께 MCP 서버 컨테이너도
기동됩니다.

```bash
docker compose up --build mcp
```

컨테이너가 기동되면 `http://localhost:8100/mcp` 로 동일하게 Inspector를 연결할
수 있습니다.

## 테스트

```bash
cd src/mcp
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

- `tests/test_neis_client.py`: NEIS 클라이언트 단위 테스트 (respx로 HTTP 모킹)
- `tests/test_services.py`: 날짜 검증·데이터 가공 로직 단위 테스트
- `tests/test_server.py`: `search_schools`, `get_meals` 도구 통합 테스트 (NEIS 클라이언트 모킹)
