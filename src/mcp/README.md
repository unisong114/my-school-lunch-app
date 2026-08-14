# MCP 서버

급식배틀용 MCP 서버입니다. 백엔드와 독립적으로 실행되며 NEIS 공개 API를 직접 호출합니다.

## 요구 사항

- Python 3.11+
- `mcp>=1.28,<2`

## 설치

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 실행

기본값은 `MCP_HOST=0.0.0.0`, `MCP_PORT=9001`, 경로는 `/mcp` 입니다.

```powershell
$env:NEIS_API_KEY=""
$env:MCP_HOST="0.0.0.0"
$env:MCP_PORT="9001"
.\.venv\Scripts\python.exe -m app.server
```

## 제공 도구

- `search_schools(name)`
- `get_meals(edu_office_code, school_code, from_date, to_date)`

성공 응답은 MCP `TextContent` 에 JSON으로 직렬화되어 반환됩니다. `get_meals` 는 같은 JSON 객체를 `structuredContent` 로도 제공합니다.

## MCP Inspector

서버를 실행한 뒤 Inspector를 띄우고 Streamable HTTP 서버 URL에 `http://localhost:9001/mcp` 를 입력합니다.

```powershell
npx @modelcontextprotocol/inspector
```

## 테스트

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
```
