#!/usr/bin/env bash
# 급식 배틀 앱을 Docker Compose 로 한 번에 빌드하고 실행합니다.
# 사용법: ./run.sh
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -f .env ]; then
  cp .env.example .env
  echo ".env 파일을 생성했습니다. NEIS_API_KEY 값을 채워주세요."
fi

echo "Docker Compose 로 앱을 빌드하고 실행합니다..."
docker compose up --build

# 실행 후 접속 주소:
#   프론트엔드: http://localhost:8080
#   백엔드 API 문서: http://localhost:8000/docs
