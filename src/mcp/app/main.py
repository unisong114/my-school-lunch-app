"""MCP 서버 진입점.

Streamable HTTP 전송으로 MCP 서버를 실행합니다::

    python -m app.main

환경 변수 ``MCP_HOST`` / ``MCP_PORT`` 로 바인딩 주소를 변경할 수 있습니다
(기본값 ``0.0.0.0:8100``). 서버가 시작되면 ``http://<host>:<port>/mcp`` 엔드포인트로
MCP 클라이언트(예: MCP Inspector)가 연결할 수 있습니다.
"""

from __future__ import annotations

from .server import mcp


def main() -> None:
    """Streamable HTTP 전송으로 MCP 서버를 실행합니다."""
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
