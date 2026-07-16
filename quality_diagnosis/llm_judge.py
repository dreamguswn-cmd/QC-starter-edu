from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv

from quality_diagnosis.judge_prompt import SYSTEM_PROMPT, build_judge_payload
from utils.pipeline import analyze_voc


ROOT = Path(__file__).resolve().parent
DEFAULT_REPORT = ROOT / "reports" / "llm_judge_result.csv"


def load_json(name: str) -> Any:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def _response_schema(rubric: dict[str, Any]) -> dict[str, Any]:
    dimensions = rubric["dimensions"]
    return {
        "type": "object",
        "properties": {
            "dimension_scores": {
                "type": "object",
                "properties": {key: {"type": "integer"} for key in dimensions},
                "required": list(dimensions),
                "additionalProperties": False,
            },
            "dimension_reasons": {
                "type": "object",
                "properties": {key: {"type": "string"} for key in dimensions},
                "required": list(dimensions),
                "additionalProperties": False,
            },
            "critical_failures": {"type": "array", "items": {"type": "string"}},
            "improvements": {"type": "array", "items": {"type": "string"}},
            "overall_reason": {"type": "string"},
        },
        "required": [
            "dimension_scores", "dimension_reasons", "critical_failures",
            "improvements", "overall_reason",
        ],
        "additionalProperties": False,
    }


def _deployment_decision(score: int, critical: bool, rubric: dict[str, Any]) -> str:
    if critical:
        return "배포 보류"
    for band in rubric["deployment_bands"]:
        if score >= band["minimum"]:
            return band["decision"]
    return "배포 보류"


def normalize_judgement(data: dict[str, Any], rubric: dict[str, Any]) -> dict[str, Any]:
    raw_scores = data["dimension_scores"]
    for key, spec in rubric["dimensions"].items():
        score = raw_scores.get(key)
        if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
            raise ValueError(f"{key} 점수는 0~100의 정수여야 합니다: {score!r}")

    percentage_scale = any(
        raw_scores[key] > spec["weight"] for key, spec in rubric["dimensions"].items()
    )
    if percentage_scale:
        scores = {
            key: round(raw_scores[key] * spec["weight"] / 100)
            for key, spec in rubric["dimensions"].items()
        }
    else:
        scores = dict(raw_scores)

    total = sum(scores.values())
    critical = bool(data["critical_failures"])
    passed = total >= rubric["pass_score"] and not critical
    return {
        **data,
        "dimension_scores": scores,
        "score_normalization": "100점 비율을 배점으로 환산" if percentage_scale else "배점 직접 채점",
        "judge": "Anthropic Independent LLM Judge",
        "model": os.getenv("ANTHROPIC_JUDGE_MODEL", "claude-sonnet-4-6"),
        "score": total,
        "pass": passed,
        "critical_failure": critical,
        "deployment_decision": _deployment_decision(total, critical, rubric),
    }


def judge_pipeline_result(
    case: dict[str, Any],
    pipeline_result: dict[str, Any],
    *,
    client: Anthropic | None = None,
    rubric: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rubric = rubric or load_json("judge_rubric.json")
    client = client or Anthropic()
    message = client.messages.create(
        model=os.getenv("ANTHROPIC_JUDGE_MODEL", "claude-sonnet-4-6"),
        max_tokens=3000,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_judge_payload(case, pipeline_result, rubric)}],
        output_config={"format": {"type": "json_schema", "schema": _response_schema(rubric)}},
    )
    raw = "".join(
        block.text for block in message.content if getattr(block, "type", "") == "text"
    )
    if message.stop_reason == "max_tokens":
        raise ValueError("Anthropic Judge 응답이 토큰 한도에서 잘렸습니다.")
    if not raw.strip():
        raise ValueError(f"Anthropic이 텍스트 응답을 반환하지 않았습니다 (stop_reason={message.stop_reason})")
    return normalize_judgement(json.loads(raw), rubric)


def run_judge_cases(limit: int | None = None) -> list[dict[str, Any]]:
    load_dotenv(ROOT.parent.parent / ".env")
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY가 필요합니다.")
    cases = load_json("judge_cases.json")[:limit]
    client = Anthropic()
    rows = []
    for case in cases:
        pipeline_result = analyze_voc(case["question"], case.get("fault"))
        judgement = judge_pipeline_result(case, pipeline_result, client=client)
        rows.append({"case": case, "pipeline_result": pipeline_result, "judgement": judgement})
    return rows


def write_csv(results: list[dict[str, Any]], path: Path = DEFAULT_REPORT) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    dimensions = list(load_json("judge_rubric.json")["dimensions"])
    fields = [
        "case_id", "question", *dimensions, "score", "pass", "critical_failure",
        "deployment_decision", "model", "overall_reason", "improvements",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for item in results:
            judgement = item["judgement"]
            row = {
                "case_id": item["case"]["case_id"],
                "question": item["case"]["question"],
                **judgement["dimension_scores"],
                "score": judgement["score"],
                "pass": judgement["pass"],
                "critical_failure": judgement["critical_failure"],
                "deployment_decision": judgement["deployment_decision"],
                "model": judgement["model"],
                "overall_reason": judgement["overall_reason"],
                "improvements": " | ".join(judgement["improvements"]),
            }
            writer.writerow(row)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="독립 Anthropic LLM Judge QA 실행")
    parser.add_argument("--limit", type=int, default=None, help="실행할 케이스 수")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    results = run_judge_cases(args.limit)
    report = write_csv(results, args.report)
    passed = sum(item["judgement"]["pass"] for item in results)
    print(f"LLM Judge: {passed}/{len(results)} PASS | report={report}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
