# 에이전트 앱 (FastAPI + Microsoft Agent Framework + GitHub Copilot SDK)

두 학교의 **같은 날짜 중식**을 비교하는 멀티에이전트 앱입니다.  
4개의 전문 평가자 에이전트가 병렬 평가를 수행하고, 앱이 루브릭 공식으로 총점을 계산한 뒤, 최종 평가자 에이전트가 **품질 게이트만** 수행합니다.

## 검증한 패키지 / 실제 API

- `agent-framework==1.14.0`
- `agent-framework-github-copilot==1.0.2`
- `agent-framework-devui==1.0.0b260813`
- `github-copilot-sdk==1.0.2`
- `ag-ui-protocol==0.1.19`
- `fastapi==0.138.0`
- `uvicorn[standard]==0.52.3`
- `httpx==0.28.1`
- `pydantic==2.13.4`
- `pydantic-settings==2.15.0`

실제 확인한 차이점:

1. `github-copilot-sdk`의 Python import 경로는 `github_copilot_sdk`가 아니라 **`copilot`** 입니다.
2. AG-UI 패키지 import 경로는 `ag_ui_protocol`이 아니라 **`ag_ui`** 입니다.
3. `ConcurrentBuilder`는 `agent_framework.orchestrations.ConcurrentBuilder`에서 사용했습니다.
4. `GitHubCopilotAgent`가 직접 토큰 env를 읽는 전용 설정 객체를 제공하지 않아, 실제 SDK의 `copilot.CopilotClient(github_token=...)` 경로도 함께 반영했습니다.

## 디렉터리 구조

```text
agent/
├─ app/
├─ tests/
├─ requirements.txt
├─ requirements-dev.txt
├─ Dockerfile
├─ .dockerignore
├─ pytest.ini
├─ devui_main.py
└─ README.md
```

## 설치

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
```

## 환경 변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `MCP_SERVER_URL` | `http://localhost:9001/mcp` | 급식 MCP 서버 URL |
| `CORS_ALLOW_ORIGINS` | `*` | 쉼표 구분 허용 Origin |
| `HOST` | `0.0.0.0` | 서버 바인드 호스트 |
| `PORT` | `9100` | 서버 포트 |
| `GITHUB_TOKEN` | 없음 | 선택적 GitHub 토큰. 없으면 Copilot CLI 로그인 세션 사용 |
| `GITHUB_COPILOT_CLI_PATH` | 없음 | Copilot CLI 실행 파일 경로 |
| `GITHUB_COPILOT_MODEL` | 없음 | 사용할 Copilot 모델 |
| `GITHUB_COPILOT_TIMEOUT` | 없음 | Copilot 요청 타임아웃 |
| `GITHUB_COPILOT_LOG_LEVEL` | 없음 | Copilot CLI 로그 레벨 |
| `GITHUB_COPILOT_BASE_DIRECTORY` | 없음 | Copilot 상태 저장 디렉터리 |

## 실행

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 9100 --reload
```

- 헬스 체크: `GET http://localhost:9100/health`

## `/agui` 요청 계약

`POST /agui` 는 **SSE(`text/event-stream`)** 를 반환합니다.

### 요청 JSON

```json
{
  "thread_id": "thread-123",
  "run_id": "run-123",
  "parent_run_id": null,
  "messages": [
    {
      "role": "user",
      "content": "서울고와 경기고를 비교해 줘"
    }
  ],
  "state": {
    "schoolA": {
      "eduOfficeCode": "B10",
      "schoolCode": "7010569",
      "schoolName": "서울고"
    },
    "schoolB": {
      "eduOfficeCode": "B10",
      "schoolCode": "7010536",
      "schoolName": "경기고"
    },
    "date": "2026-08-14",
    "prompt": "두 학교 급식의 장단점과 개선안을 비교해 주세요."
  },
  "forwarded_props": {}
}
```

### 요청 규칙

- `state` 또는 `forwarded_props` 중 한 곳에는 반드시 아래 값이 있어야 합니다.
  - `schoolA`
  - `schoolB`
  - `date`
  - `prompt`
- `schoolA`와 `schoolB`는 동일한 학교일 수 없습니다.
- `date`는 `YYYY-MM-DD` 형식이어야 합니다.

### 4xx 오류 예시

```json
{
  "detail": "같은 학교를 두 번 선택할 수 없습니다."
}
```

## `/agui` SSE 응답 계약

이 엔드포인트는 다음 순서의 이벤트를 보냅니다.

1. `RUN_STARTED`
2. `TEXT_MESSAGE_START`
3. 0개 이상 `TEXT_MESSAGE_CONTENT`
4. `TEXT_MESSAGE_END`
5. `CUSTOM` (`name = "lunch_battle_result"`)
6. `RUN_FINISHED`

오류 시에는 `RUN_ERROR`를 보냅니다.

### 최종 결과 이벤트 예시

```text
data: {"type":"CUSTOM","name":"lunch_battle_result","value":{"schoolA":{"eduOfficeCode":"B10","schoolCode":"7010569","schoolName":"서울고","totalScore":81.0,"areas":{"nutritionBalance":{"score":4,"weightedScore":32.0,"rationale":"열량과 식품군 구성이 비교적 균형적입니다."},"healthiness":{"score":4,"weightedScore":20.0,"rationale":"튀김 비중이 낮고 부담 요인이 적습니다."},"menuQuality":{"score":5,"weightedScore":20.0,"rationale":"메뉴 조화와 식재료 다양성이 우수합니다."},"mealParticipation":{"score":3,"weightedScore":9.0,"rationale":"급식 인원수는 확인되나 평균적인 규모입니다."}}},"schoolB":{"eduOfficeCode":"B10","schoolCode":"7010536","schoolName":"경기고","totalScore":61.0,"areas":{"nutritionBalance":{"score":3,"weightedScore":24.0,"rationale":"구성은 갖췄지만 채소 다양성이 아쉽습니다."},"healthiness":{"score":3,"weightedScore":15.0,"rationale":"가공식품과 당류 신호가 일부 보입니다."},"menuQuality":{"score":4,"weightedScore":16.0,"rationale":"전반적으로 무난하지만 일부 중복이 있습니다."},"mealParticipation":{"score":2,"weightedScore":6.0,"rationale":"급식 인원수는 있으나 규모가 더 작습니다."}}},"winner":"A","summary":"학교 A가 영양 균형과 메뉴 품질에서 앞서 총점 우위를 보였습니다. 학교 B는 채소 다양성과 건강성 개선이 필요합니다.","qualityNotes":["메뉴명만으로 조리법을 단정하지 않도록 평가 근거를 유지했습니다."]}}
```

### 최종 결과 JSON shape

```json
{
  "schoolA": {
    "eduOfficeCode": "string",
    "schoolCode": "string",
    "schoolName": "string",
    "totalScore": 0,
    "areas": {
      "nutritionBalance": {
        "score": 1,
        "weightedScore": 0,
        "rationale": "string"
      },
      "healthiness": {
        "score": 1,
        "weightedScore": 0,
        "rationale": "string"
      },
      "menuQuality": {
        "score": 1,
        "weightedScore": 0,
        "rationale": "string"
      },
      "mealParticipation": {
        "score": 1,
        "weightedScore": 0,
        "rationale": "string"
      }
    }
  },
  "schoolB": {
    "eduOfficeCode": "string",
    "schoolCode": "string",
    "schoolName": "string",
    "totalScore": 0,
    "areas": {
      "nutritionBalance": {
        "score": 1,
        "weightedScore": 0,
        "rationale": "string"
      },
      "healthiness": {
        "score": 1,
        "weightedScore": 0,
        "rationale": "string"
      },
      "menuQuality": {
        "score": 1,
        "weightedScore": 0,
        "rationale": "string"
      },
      "mealParticipation": {
        "score": 1,
        "weightedScore": 0,
        "rationale": "string"
      }
    }
  },
  "winner": "A",
  "summary": "string",
  "qualityNotes": ["string"]
}
```

`winner` 값은 `"A"`, `"B"`, `"tie"` 중 하나입니다.

## 점수 계산 방식

- 영역별 평점: 1~5
- 가중치:
  - `nutritionBalance`: 40
  - `healthiness`: 25
  - `menuQuality`: 20
  - `mealParticipation`: 15
- 공식: **`(평점 / 5) × 가중치`**
- 각 영역 환산 점수는 소수 첫째 자리까지 표시
- 총점이 같으면 `winner = "tie"`

## 테스트

```powershell
.\.venv\Scripts\Activate.ps1
pytest
```

- 단위 테스트: `tests/test_scoring.py`, `tests/test_validation.py`
- 통합 테스트: `tests/test_agui_endpoint.py`

## DevUI 실행

실제 확인한 DevUI 진입점은 `agent_framework.devui.serve(...)` 와 `devui` CLI 입니다.

### 스크립트 방식

```powershell
.\.venv\Scripts\Activate.ps1
python devui_main.py
```

- 기본 URL: `http://127.0.0.1:8181`
- 이 스크립트는 **Concurrent workflow 자체**를 DevUI에 등록합니다.

### CLI 방식

```powershell
.\.venv\Scripts\Activate.ps1
devui . --port 8181 --no-auth
```

CLI는 현재 디렉터리의 엔티티를 스캔합니다. 이 저장소에서는 스크립트 방식이 더 명시적입니다.
