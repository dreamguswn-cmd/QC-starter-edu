from __future__ import annotations

import json
from typing import Any


SYSTEM_PROMPT = """당신은 VOC 분석 파이프라인과 독립된 QA 심사자입니다.
사용자 질문, 검색 근거, 6개 Agent의 중간 결과와 최종 산출물만 평가하세요.
제공되지 않은 사실이나 정책을 만들지 마세요. 각 점수에는 간결한 근거를 제시하세요.
dimension_scores는 100점 비율이 아니라 정확성 0~25, 요약 충실성 0~20,
개선안 구체성 0~20, 유용성 0~20, 안전성 0~15의 배점 범위로 직접 채점하세요.
critical failure가 하나라도 있으면 총점과 관계없이 FAIL입니다.
반드시 지정된 JSON 스키마로만 응답하세요."""


def build_judge_payload(
    case: dict[str, Any], pipeline_result: dict[str, Any], rubric: dict[str, Any]
) -> str:
    return json.dumps(
        {"test_case": case, "pipeline_result": pipeline_result, "rubric": rubric},
        ensure_ascii=False,
    )
