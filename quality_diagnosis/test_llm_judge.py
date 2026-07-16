from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from quality_diagnosis.llm_judge import (
    judge_pipeline_result,
    load_json,
    normalize_judgement,
    run_judge_cases,
    write_csv,
)


VALID_RESPONSE = {
    "dimension_scores": {
        "accuracy": 23,
        "summary_fidelity": 18,
        "action_specificity": 17,
        "usefulness": 18,
        "safety": 15,
    },
    "dimension_reasons": {
        "accuracy": "검색 근거와 일치함",
        "summary_fidelity": "핵심 불만을 보존함",
        "action_specificity": "담당자와 조치가 구체적임",
        "usefulness": "고객과 운영자가 활용 가능함",
        "safety": "단정과 개인정보 노출이 없음",
    },
    "critical_failures": [],
    "improvements": ["처리 기한을 명시하세요."],
    "overall_reason": "근거 기반의 안전하고 실행 가능한 결과입니다.",
}


class FakeMessages:
    def __init__(self, payload):
        self.payload = payload
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text=json.dumps(self.payload, ensure_ascii=False))],
            stop_reason="end_turn",
        )


class FakeClient:
    def __init__(self, payload=VALID_RESPONSE):
        self.messages = FakeMessages(payload)


def test_independent_judge_uses_structured_output_and_scores_result():
    client = FakeClient()
    result = judge_pipeline_result(
        {"case_id": "JUDGE-TEST", "question": "배송이 늦어요."},
        {"success": True, "steps": [], "final": {}},
        client=client,
    )
    assert result["judge"] == "Anthropic Independent LLM Judge"
    assert result["score"] == 91
    assert result["pass"] is True
    assert result["deployment_decision"] == "배포 가능"
    assert client.messages.kwargs["model"] == "claude-sonnet-4-6"
    assert client.messages.kwargs["output_config"]["format"]["type"] == "json_schema"


def test_critical_failure_always_blocks_deployment():
    response = {**VALID_RESPONSE, "critical_failures": ["근거에 없는 환불 확정 안내"]}
    result = normalize_judgement(response, load_json("judge_rubric.json"))
    assert result["score"] == 91
    assert result["pass"] is False
    assert result["deployment_decision"] == "배포 보류"


def test_out_of_range_dimension_score_is_rejected():
    response = json.loads(json.dumps(VALID_RESPONSE))
    response["dimension_scores"]["safety"] = 101
    with pytest.raises(ValueError, match="safety 점수"):
        normalize_judgement(response, load_json("judge_rubric.json"))


def test_percentage_scores_are_converted_to_weighted_points():
    response = json.loads(json.dumps(VALID_RESPONSE))
    response["dimension_scores"] = {key: 80 for key in response["dimension_scores"]}
    result = normalize_judgement(response, load_json("judge_rubric.json"))
    assert result["dimension_scores"] == {
        "accuracy": 20,
        "summary_fidelity": 16,
        "action_specificity": 16,
        "usefulness": 16,
        "safety": 12,
    }
    assert result["score"] == 80
    assert result["score_normalization"] == "100점 비율을 배점으로 환산"


def test_csv_report_is_created(tmp_path: Path):
    judgement = normalize_judgement(VALID_RESPONSE, load_json("judge_rubric.json"))
    path = write_csv(
        [{"case": {"case_id": "JUDGE-TEST", "question": "배송이 늦어요."}, "judgement": judgement}],
        tmp_path / "llm_judge_result.csv",
    )
    text = path.read_text(encoding="utf-8-sig")
    assert "JUDGE-TEST" in text
    assert "Anthropic Independent LLM Judge" not in text
    assert "배포 가능" in text


@pytest.mark.skipif(
    os.getenv("RUN_LLM_JUDGE_TESTS") != "1",
    reason="실제 API 비용이 드는 테스트입니다. RUN_LLM_JUDGE_TESTS=1로 활성화하세요.",
)
def test_live_anthropic_llm_judge():
    results = run_judge_cases(limit=1)
    assert results[0]["judgement"]["judge"] == "Anthropic Independent LLM Judge"
    assert "warning" not in results[0]["judgement"]
