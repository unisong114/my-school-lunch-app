"""요청 검증 테스트."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_missing_school_field_returns_korean_422(validation_app) -> None:
    client = TestClient(validation_app)
    response = client.post(
        "/agui",
        json={
            "thread_id": "thread-1",
            "run_id": "run-1",
            "messages": [],
            "state": {
                "schoolA": {
                    "eduOfficeCode": "B10",
                    "schoolCode": "7010569",
                    "schoolName": "서울고",
                },
                "date": "2026-08-14",
                "prompt": "비교해 주세요.",
            },
        },
    )

    assert response.status_code == 422
    assert "schoolB" in response.json()["detail"]


def test_duplicate_school_returns_400(validation_app) -> None:
    client = TestClient(validation_app)
    response = client.post(
        "/agui",
        json={
            "thread_id": "thread-1",
            "run_id": "run-1",
            "messages": [],
            "state": {
                "schoolA": {
                    "eduOfficeCode": "B10",
                    "schoolCode": "7010569",
                    "schoolName": "서울고",
                },
                "schoolB": {
                    "eduOfficeCode": "B10",
                    "schoolCode": "7010569",
                    "schoolName": "서울고",
                },
                "date": "2026-08-14",
                "prompt": "비교해 주세요.",
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "같은 학교를 두 번 선택할 수 없습니다."


def test_bad_date_returns_korean_422(validation_app) -> None:
    client = TestClient(validation_app)
    response = client.post(
        "/agui",
        json={
            "thread_id": "thread-1",
            "run_id": "run-1",
            "messages": [],
            "state": {
                "schoolA": {
                    "eduOfficeCode": "B10",
                    "schoolCode": "7010569",
                    "schoolName": "서울고",
                },
                "schoolB": {
                    "eduOfficeCode": "B10",
                    "schoolCode": "7010536",
                    "schoolName": "경기고",
                },
                "date": "20260814",
                "prompt": "비교해 주세요.",
            },
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "date는 YYYY-MM-DD 형식이어야 합니다."
