"""평가 루브릭 로더."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


AREA_SECTIONS: dict[str, tuple[str, str]] = {
    "nutritionBalance": ("## 1. 영양 균형 (40%)", "## 2. 건강성 (25%)"),
    "healthiness": ("## 2. 건강성 (25%)", "## 3. 식재료 및 메뉴 품질 (20%)"),
    "menuQuality": ("## 3. 식재료 및 메뉴 품질 (20%)", "## 4. 급식 참여도 (15%)"),
    "mealParticipation": ("## 4. 급식 참여도 (15%)", "## 최종 평가자 품질 게이트"),
}


@dataclass(frozen=True)
class RubricSections:
    """루브릭 주요 섹션."""

    purpose: str
    data_limits: str
    quality_gate: str
    areas: dict[str, str]


def _extract_between(text: str, start: str, end: str | None = None) -> str:
    start_index = text.index(start)
    end_index = text.index(end, start_index) if end else len(text)
    return text[start_index:end_index].strip()


@lru_cache
def load_rubric_sections() -> RubricSections:
    """루브릭 파일을 읽고 필요한 섹션만 분리합니다."""

    root = Path(__file__).resolve().parents[2]
    rubric_path = root / "EVALUATION_RUBRIC.md"
    text = rubric_path.read_text(encoding="utf-8")

    purpose = _extract_between(text, "## 목적", "## 1. 영양 균형 (40%)")
    data_limits = _extract_between(text, "## 데이터 한계")
    quality_gate = _extract_between(text, "## 최종 평가자 품질 게이트", "## 데이터 한계")
    areas = {
        key: _extract_between(text, start, end)
        for key, (start, end) in AREA_SECTIONS.items()
    }
    return RubricSections(
        purpose=purpose,
        data_limits=data_limits,
        quality_gate=quality_gate,
        areas=areas,
    )
