from __future__ import annotations

import json
import time
from typing import Any

from llm_wrappers.judge import anthropic_judge, rule_judge
from utils.pipeline import analyze_voc


VALIDATION_CASES = [
    {"id":"V-01","type":"일반 불만","question":"배송이 이틀 늦었습니다.","expected":["배송","늦"],"check":"핵심 내용 요약"},
    {"id":"V-02","type":"복합 불만","question":"배송 지연과 상담원 불친절이 모두 불만입니다.","expected":["배송","상담"],"check":"여러 불만을 빠짐없이 추출"},
    {"id":"V-03","type":"짧고 모호한 불만","question":"너무 별로예요.","expected":[],"check":"근거 없는 추측 방지"},
    {"id":"V-04","type":"긴 불만","question":"주문한 상품이 늦게 도착했고 포장이 파손되어 교환을 요청했지만 상담 연결도 지연됐으며 결국 환불 처리 상태도 안내받지 못했습니다.","expected":["주문","파손","환불"],"check":"핵심 정보 압축"},
    {"id":"V-05","type":"감정적 표현","question":"배송 안내가 계속 바뀌어 너무 화가 나고 다시는 이용하지 않겠습니다.","expected":["배송"],"check":"감정과 사실 구분"},
    {"id":"V-06","type":"오탈자·구어체","question":"배송도 늦구 환불도 안댐", "expected":["배송","환불"],"check":"의미를 정상적으로 이해"},
    {"id":"V-07","type":"개인정보 포함","question":"홍길동입니다. 전화번호 010-1234-5678, 이메일 test@example.com으로 환불 결과를 알려주세요.","expected":["환불"],"check":"개인정보 마스킹","pii":True},
    {"id":"V-08","type":"위험 표현","question":"처리하지 않으면 신고하고 고소하겠습니다.","expected":["신고","고소"],"check":"과도한 판단 없이 적절히 대응","risk":True},
    {"id":"V-09","type":"정상·칭찬 데이터","question":"상담원이 친절하게 처리해 주셨습니다.","expected":["친절"],"check":"불만으로 잘못 분류하지 않음","praise":True},
    {"id":"V-10","type":"입력 이상","question":"!!!@@@###", "expected":[],"check":"오류 없이 안전하게 처리","abnormal":True},
]


def _case_for_judge(case: dict[str, Any]) -> dict[str, Any]:
    return {"case_id":case["id"], "question":case["question"], "expected_keywords":case["expected"],
            "required_output":["고객 안내","개선안"], "prohibited_output":["개인정보 요구"]}


def run_validation_case(case: dict[str, Any], use_independent_judge: bool = False) -> dict[str, Any]:
    started = time.perf_counter()
    result = analyze_voc(case["question"])
    elapsed_ms = max(1, int((time.perf_counter() - started) * 1000))
    serialized = json.dumps(result, ensure_ascii=False)
    final = result.get("final") or {}
    analysis = final.get("analysis") or {}
    improvement = final.get("improvement") or {}
    interpreted = (result.get("steps") or [{}])[0].get("output", {})
    source_text = " ".join([interpreted.get("normalized_question", ""), analysis.get("summary", ""), serialized])

    coverage = 1.0 if not case["expected"] else sum(term in source_text for term in case["expected"]) / len(case["expected"])
    safe_ambiguous = not case.get("abnormal") or bool(result.get("success"))
    if case["type"] == "짧고 모호한 불만":
        safe_ambiguous = interpreted.get("is_ambiguous", False) and not analysis.get("facts")
    privacy_ok = not case.get("pii") or ("010-1234-5678" not in serialized and "test@example.com" not in serialized)
    praise_ok = not case.get("praise") or interpreted.get("is_praise", False)
    risk_ok = not case.get("risk") or interpreted.get("requires_careful_response", False)
    summary_pass = coverage >= .8 and safe_ambiguous and privacy_ok and praise_ok and risk_ok

    actions = improvement.get("improvement_actions") or []
    cause = improvement.get("root_cause_hypothesis") or ""
    cause_improvement_pass = bool(actions) and bool(cause) and (bool(analysis.get("limitations")) or bool(analysis.get("facts")))

    judge_case = _case_for_judge(case)
    baseline = rule_judge(judge_case, result)
    independent = anthropic_judge(judge_case, result) if use_independent_judge else None
    cross_model_pass = None if independent is None else bool(independent.get("pass")) == bool(baseline.get("pass"))
    error = not result.get("final") or len(result.get("steps", [])) != 6
    return {"case":case, "result":result, "summary_pass":summary_pass,
            "summary_coverage":round(coverage * 100, 1), "cause_improvement_pass":cause_improvement_pass,
            "rule_judge":baseline, "independent_judge":independent, "cross_model_pass":cross_model_pass,
            "privacy_ok":privacy_ok, "error":error, "response_time_ms":elapsed_ms}


def run_three_axis_validation(use_independent_judge: bool = False) -> list[dict[str, Any]]:
    return [run_validation_case(case, use_independent_judge) for case in VALIDATION_CASES]


def validation_metrics(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = max(1, len(results))
    passed = sum(r["summary_pass"] and r["cause_improvement_pass"] for r in results)
    scores = [r["independent_judge"].get("score", 0) if r["independent_judge"] else r["rule_judge"].get("score", 0) for r in results]
    cross = [r["cross_model_pass"] for r in results if r["cross_model_pass"] is not None]
    values = {
        "전체 테스트 통과율": passed / total * 100,
        "평균 Judge 점수": sum(scores) / len(scores) if scores else 0,
        "사실 정확성": sum(r["summary_coverage"] for r in results) / total,
        "개인정보 마스킹": sum(r["privacy_ok"] for r in results if r["case"].get("pii")) / max(1, sum(bool(r["case"].get("pii")) for r in results)) * 100,
        "오류율": sum(r["error"] for r in results) / total * 100,
        "평균 응답시간": sum(r["response_time_ms"] for r in results) / total / 1000,
    }
    targets = {"전체 테스트 통과율":90, "평균 Judge 점수":80, "사실 정확성":90, "개인정보 마스킹":100, "오류율":5, "평균 응답시간":10}
    return [{"지표":name, "목표":f"{target}{'초 이하' if name == '평균 응답시간' else '% 이하' if name == '오류율' else '점 이상' if name == '평균 Judge 점수' else '%' if name == '개인정보 마스킹' else '% 이상'}",
             "실제 결과":f"{value:.1f}{'초' if name == '평균 응답시간' else '점' if name == '평균 Judge 점수' else '%'}",
             "판정":"PASS" if (value <= target if name in ["오류율","평균 응답시간"] else value >= target) else "FAIL"}
            for name, value in values.items() for target in [targets[name]]]
