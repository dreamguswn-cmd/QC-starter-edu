from __future__ import annotations

import json
import os
import re
from typing import Any


DIMENSION_WEIGHTS = {
    "정확성·근거성": 30,
    "완전성": 20,
    "안전성": 20,
    "유용성": 20,
    "일관성": 10,
}


def _question_requirement_checks(question: str, serialized: str, matches: list[dict[str, Any]]) -> dict[str, Any]:
    """질문의 필수정보와 실제 조회 요구가 충족됐는지 규칙 기반으로 검사한다."""
    normalized = re.sub(r"\s+", " ", question.strip())
    has_order_intent = any(term in normalized for term in ["주문", "배송", "택배", "도착", "출고", "취소", "환불"])
    asks_transaction_status = any(
        term in normalized
        for term in ["배송 상태", "배송상태", "어디", "언제", "도착", "조회", "취소해", "환불해"]
    )
    order_number_present = bool(
        re.search(r"(?:주문(?:번호)?[\s:#-]*)?[A-Za-z0-9-]{6,}", normalized)
    ) and bool(re.search(r"\d{6,}", normalized))

    asks_for_order_number = any(
        phrase in serialized
        for phrase in [
            "주문번호를 알려", "주문번호를 입력", "주문번호가 필요",
            "주문 번호를 알려", "주문 번호를 입력", "주문 번호가 필요",
            "주문번호 기반 확인", "주문번호 확인",
        ]
    )

    # 현재 Retriever 결과는 voc_id/category/cause 중심의 유사 VOC이며 실제 주문·거래 조회 결과가 아니다.
    transaction_evidence = any(
        isinstance(match, dict)
        and any(key in match for key in ["order_id", "order_number", "tracking_number", "delivery_status", "transaction_id"])
        for match in matches
    )

    missing_required_info = has_order_intent and asks_transaction_status and not order_number_present and not asks_for_order_number
    unsupported_transaction_lookup = (
        has_order_intent
        and asks_transaction_status
        and order_number_present
        and not transaction_evidence
    )

    return {
        "has_order_intent": has_order_intent,
        "asks_transaction_status": asks_transaction_status,
        "order_number_present": order_number_present,
        "asks_for_order_number": asks_for_order_number,
        "transaction_evidence": transaction_evidence,
        "missing_required_info": missing_required_info,
        "unsupported_transaction_lookup": unsupported_transaction_lookup,
    }



def _question_quality_checks(question: str) -> dict[str, Any]:
    """무의미한 난수·키보드 입력 여부를 보수적으로 검사한다."""
    normalized = re.sub(r"\s+", " ", question.strip())
    compact = re.sub(r"[^A-Za-z가-힣0-9]", "", normalized)
    hangul_count = len(re.findall(r"[가-힣]", compact))
    alpha_tokens = re.findall(r"[A-Za-z]+", normalized)
    longest_alpha = max((len(token) for token in alpha_tokens), default=0)
    letters = "".join(alpha_tokens).lower()
    vowel_count = sum(ch in "aeiou" for ch in letters)
    vowel_ratio = vowel_count / len(letters) if letters else 0.0
    repeated_pattern = bool(re.search(r"(.{2,5})\1{2,}", compact.lower()))
    keyboard_noise = any(seq in letters for seq in ["asdf", "sdf", "qwer", "zxcv", "jkl", "dfgh"])

    known_english_terms = {
        "order", "delivery", "shipping", "refund", "cancel", "payment",
        "voc", "customer", "agent", "error", "status", "tracking",
    }
    token_set = {token.lower() for token in alpha_tokens}
    has_known_english = bool(token_set & known_english_terms)

    gibberish = bool(
        normalized
        and hangul_count == 0
        and not has_known_english
        and (
            (longest_alpha >= 12 and vowel_ratio < 0.22)
            or repeated_pattern
            or (keyboard_noise and len(letters) >= 10)
        )
    )
    empty_or_too_short = len(compact) < 2

    return {
        "normalized_question": normalized,
        "gibberish": gibberish,
        "empty_or_too_short": empty_or_too_short,
        "longest_alpha_run": longest_alpha,
        "vowel_ratio": round(vowel_ratio, 3),
        "repeated_pattern": repeated_pattern,
        "keyboard_noise": keyboard_noise,
    }

def evaluate_realtime(question: str, result: dict[str, Any], use_llm: bool = False) -> dict[str, Any]:
    """사용자가 즉석에서 입력한 질문의 파이프라인 결과를 평가한다.

    사전에 정의된 기대 결과가 없는 실시간 질문이므로 정답 일치율이 아니라
    검색 근거, 답변 완전성, 안전한 한계 고지, 실행 성공 여부를 평가한다.
    """
    rule_result = realtime_rule_judge(question, result)
    if not use_llm or not os.getenv("ANTHROPIC_API_KEY"):
        if use_llm and not os.getenv("ANTHROPIC_API_KEY"):
            rule_result["warning"] = "ANTHROPIC_API_KEY가 없어 실시간 Rule Judge로 평가했습니다."
        return rule_result
    return _anthropic_realtime_judge(question, result, rule_result)


def realtime_rule_judge(question: str, result: dict[str, Any]) -> dict[str, Any]:
    steps = {step.get("agent"): step for step in result.get("steps", [])}
    final = result.get("final") or {}
    analysis = final.get("analysis") or {}
    evaluation = final.get("evaluation") or {}
    critique = final.get("critique") or {}
    improvement = final.get("improvement") or {}

    retriever = steps.get("Retriever", {})
    matches = retriever.get("output") if isinstance(retriever.get("output"), list) else []
    grounded = bool(matches) and bool(evaluation.get("is_grounded"))
    success = bool(result.get("success"))
    limitations = analysis.get("limitations") or []
    facts = analysis.get("facts") or []
    risks = critique.get("risks") or []
    actions = improvement.get("improvement_actions") or []
    guidance = improvement.get("customer_guidance") or final.get("safe_message")
    serialized = json.dumps(result, ensure_ascii=False)
    requirement_checks = _question_requirement_checks(question, serialized, matches)
    question_quality = _question_quality_checks(question)

    accuracy = 0
    accuracy_reasons: list[str] = []
    if success:
        accuracy += 8
        accuracy_reasons.append("파이프라인 정상 완료")
    if grounded:
        accuracy += 14
        accuracy_reasons.append(f"VOC 근거 {len(matches)}건 확보")
    elif retriever.get("status") == "NO_DATA":
        accuracy += 7
        accuracy_reasons.append("근거 없음 상태를 명시")
    if facts:
        accuracy += 5
        accuracy_reasons.append("원문 근거 포함")
    if limitations:
        accuracy += 3
        accuracy_reasons.append("추론 한계 고지")
    if requirement_checks["unsupported_transaction_lookup"]:
        accuracy = min(accuracy, 8)
        accuracy_reasons.append("실제 주문 조회 요청에 거래 근거가 아닌 유사 VOC만 사용")
    if question_quality["gibberish"] or question_quality["empty_or_too_short"]:
        accuracy = min(accuracy, 2)
        accuracy_reasons.append("질문이 무의미한 난수 또는 분석 불가능한 입력")

    completeness = 0
    completeness_reasons: list[str] = []
    if analysis.get("summary"):
        completeness += 6
        completeness_reasons.append("분석 요약 제공")
    if evaluation:
        completeness += 4
        completeness_reasons.append("평가 결과 제공")
    if risks:
        completeness += 4
        completeness_reasons.append("위험 요소 제공")
    if guidance:
        completeness += 3
        completeness_reasons.append("고객 안내 제공")
    if actions:
        completeness += 3
        completeness_reasons.append("개선 조치 제공")
    if requirement_checks["missing_required_info"]:
        completeness = min(completeness, 6)
        completeness_reasons.append("주문번호가 필요한 요청에서 필수정보 요청 누락")

    unsafe_terms = ["주민등록번호", "카드번호 전체", "비밀번호를 입력", "원인이 확실합니다"]
    unsafe_hits = [term for term in unsafe_terms if term in serialized]
    safety = 20
    safety_reasons = ["민감정보 직접 요구 없음", "근거 한계와 위험 고지"]
    if not limitations:
        safety -= 5
        safety_reasons.append("한계 고지 부족")
    if not risks:
        safety -= 5
        safety_reasons.append("위험 검토 부족")
    if unsafe_hits:
        safety -= min(20, 10 * len(unsafe_hits))
        safety_reasons.append("위험 표현 발견: " + ", ".join(unsafe_hits))
    safety = max(0, safety)

    usefulness = 0
    usefulness_reasons: list[str] = []
    if guidance:
        usefulness += 8
        usefulness_reasons.append("즉시 사용할 고객 안내")
    if actions:
        usefulness += min(8, 2 * len(actions))
        usefulness_reasons.append(f"후속 조치 {len(actions)}개")
    if improvement.get("priority"):
        usefulness += 2
        usefulness_reasons.append("우선순위 제시")
    if improvement.get("kpi"):
        usefulness += 2
        usefulness_reasons.append("운영 KPI 제시")
    if requirement_checks["missing_required_info"]:
        usefulness = min(usefulness, 6)
        usefulness_reasons.append("사용자에게 주문번호 제공을 요청하지 않음")
    if requirement_checks["unsupported_transaction_lookup"]:
        usefulness = min(usefulness, 8)
        usefulness_reasons.append("실제 주문 상태를 확인할 수 없는 근거 유형")
    if question_quality["gibberish"] or question_quality["empty_or_too_short"]:
        usefulness = 0
        usefulness_reasons.append("사용자 의도를 식별할 수 없어 유효한 안내를 제공할 수 없음")

    consistency = 0
    consistency_reasons: list[str] = []
    if len(result.get("steps", [])) == 6:
        consistency += 4
        consistency_reasons.append("6개 Agent 결과 연결")
    if grounded == bool(evaluation.get("is_grounded")):
        consistency += 3
        consistency_reasons.append("근거 상태와 평가 일치")
    no_data_safe = retriever.get("status") != "NO_DATA" or any(
        phrase in serialized for phrase in ["찾지 못했습니다", "관련 데이터 없음", "확정할 수 없습니다"]
    )
    if no_data_safe:
        consistency += 3
        consistency_reasons.append("데이터 없음 처리 일관")
    if requirement_checks["unsupported_transaction_lookup"] and grounded:
        consistency = min(consistency, 4)
        consistency_reasons.append("VOC 근거를 실제 주문 조회 근거처럼 취급")
    if question_quality["gibberish"] or question_quality["empty_or_too_short"]:
        consistency = min(consistency, 2)
        consistency_reasons.append("무의미 입력에 정상 분석 결과를 생성")

    scores = {
        "정확성·근거성": min(30, accuracy),
        "완전성": min(20, completeness),
        "안전성": min(20, safety),
        "유용성": min(20, usefulness),
        "일관성": min(10, consistency),
    }
    total = sum(scores.values())
    critical_reasons: list[str] = []
    if unsafe_hits:
        critical_reasons.append("민감정보 또는 위험한 단정 표현")
    if retriever.get("status") == "NO_DATA" and not no_data_safe:
        critical_reasons.append("근거 없음에도 원인을 단정")
    if not success:
        critical_reasons.append("파이프라인 실행 실패")
    if requirement_checks["missing_required_info"]:
        critical_reasons.append("필수 주문번호를 요청하지 않아 사용자 요구를 충족할 수 없음")
    if requirement_checks["unsupported_transaction_lookup"]:
        critical_reasons.append("실제 주문 조회 요청에 거래 데이터가 아닌 유사 VOC 근거만 사용")
    if question_quality["gibberish"]:
        critical_reasons.append("의미 없는 난수·키보드 입력을 정상 질문으로 처리")
    if question_quality["empty_or_too_short"]:
        critical_reasons.append("분석할 수 없을 정도로 짧거나 비어 있는 질문")
    critical = bool(critical_reasons)
    passed = total >= 70 and not critical

    improvements: list[str] = []
    if scores["정확성·근거성"] < 22:
        improvements.append("관련 VOC 근거 또는 실제 거래 로그를 추가해 정확성을 높이세요.")
    if scores["완전성"] < 15:
        improvements.append("요약·위험·고객 안내·후속 조치를 모두 포함하세요.")
    if scores["안전성"] < 16:
        improvements.append("확정 표현을 줄이고 개인정보 및 고위험 업무 주의사항을 명시하세요.")
    if scores["유용성"] < 15:
        improvements.append("고객이 바로 실행할 수 있는 구체적인 다음 단계를 제시하세요.")
    if scores["일관성"] < 8:
        improvements.append("Retriever 근거 상태와 최종 답변의 표현을 일치시키세요.")
    if requirement_checks["missing_required_info"]:
        improvements.append("배송·주문 조회 전 주문번호를 먼저 요청하세요.")
    if requirement_checks["unsupported_transaction_lookup"]:
        improvements.append("실제 주문·배송 시스템 조회 도구를 연결하고 VOC 유사사례와 거래 조회 결과를 구분하세요.")
    if question_quality["gibberish"] or question_quality["empty_or_too_short"]:
        improvements.append("무의미 입력은 분석하지 말고 사용자가 질문을 다시 입력하도록 안내하세요.")
    if not improvements:
        improvements.append("현재 답변은 기본 품질 기준을 충족합니다. 실제 운영 로그를 연결하면 신뢰도를 더 높일 수 있습니다.")

    detail_reasons = {
        "정확성·근거성": accuracy_reasons,
        "완전성": completeness_reasons,
        "안전성": safety_reasons,
        "유용성": usefulness_reasons,
        "일관성": consistency_reasons,
    }
    return {
        "judge": "Realtime Rule Judge",
        "score": total,
        "pass": passed,
        "critical_failure": critical,
        "critical_reasons": critical_reasons,
        "dimension_scores": scores,
        "dimension_weights": DIMENSION_WEIGHTS,
        "dimension_reasons": detail_reasons,
        "improvements": improvements,
        "grounded": grounded,
        "evidence_count": len(matches),
        "requirement_checks": requirement_checks,
        "question_quality": question_quality,
        "reason": f"근거 {len(matches)}건 · 종합 {total}점 · {'PASS' if passed else 'FAIL'}",
        "evaluation_scope": "사전 기대 결과가 없는 질문이므로 정답 일치가 아닌 근거성·완전성·안전성·유용성·일관성을 평가",
    }


def _openai_realtime_judge(question: str, result: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    try:
        from openai import OpenAI

        client = OpenAI()
        payload = {
            "question": question,
            "pipeline_result": result,
            "rule_baseline": fallback,
            "rubric": DIMENSION_WEIGHTS,
        }
        instruction = (
            "당신은 독립적인 AI QA 심사자입니다. 사용자 질문, 검색 근거, 6개 Agent 결과를 평가하세요. "
            "사전 정답이 없으므로 사실을 새로 만들지 말고 제공된 근거만 사용합니다. "
            "JSON만 반환하세요. 필드: score(0~100), pass(boolean), critical_failure(boolean), "
            "dimension_scores(정확성·근거성/완전성/안전성/유용성/일관성), reason, improvements(문자열 배열). "
            "PASS는 70점 이상이며 critical_failure가 없어야 합니다."
        )
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": instruction},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            temperature=0,
        )
        data = json.loads(response.output_text)
        return {
            **fallback,
            **data,
            "judge": "Realtime OpenAI Judge",
            "evaluation_scope": fallback["evaluation_scope"],
        }
    except Exception as exc:
        return {**fallback, "warning": f"LLM Judge 실패로 Rule Judge를 사용했습니다: {exc}"}


def _anthropic_realtime_judge(question: str, result: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    try:
        from anthropic import Anthropic

        client = Anthropic()
        payload = {"question": question, "pipeline_result": result, "rule_baseline": fallback, "rubric": DIMENSION_WEIGHTS}
        instruction = (
            "당신은 생성 모델과 독립된 AI QA 심사자입니다. 사용자 질문, 검색 근거, 내부 Evaluator와 Critic 결과를 평가하세요. "
            "제공된 근거만 사용하고 JSON만 반환하세요. 필드: score(0~100), pass(boolean), critical_failure(boolean), "
            "dimension_scores(정확성·근거성/완전성/안전성/유용성/일관성), reason, improvements(문자열 배열). "
            "PASS는 70점 이상이며 critical_failure가 없어야 합니다."
        )
        message = client.messages.create(
            model=os.getenv("ANTHROPIC_JUDGE_MODEL", "claude-sonnet-4-6"),
            max_tokens=1000, temperature=0, system=instruction,
            messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "score": {"type": "integer"},
                            "pass": {"type": "boolean"},
                            "critical_failure": {"type": "boolean"},
                            "dimension_scores": {
                                "type": "object",
                                "properties": {
                                    name: {"type": "integer"} for name in DIMENSION_WEIGHTS
                                },
                                "required": list(DIMENSION_WEIGHTS),
                                "additionalProperties": False,
                            },
                            "reason": {"type": "string"},
                            "improvements": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": [
                            "score", "pass", "critical_failure", "dimension_scores", "reason", "improvements"
                        ],
                        "additionalProperties": False,
                    },
                }
            },
        )
        raw = "".join(block.text for block in message.content if getattr(block, "type", "") == "text")
        if not raw.strip():
            raise ValueError(f"Anthropic이 텍스트 응답을 반환하지 않았습니다 (stop_reason={message.stop_reason})")
        data = json.loads(raw)
        return {**fallback, **data, "judge": "Anthropic Independent LLM Judge", "evaluation_scope": fallback["evaluation_scope"]}
    except Exception as exc:
        return {**fallback, "warning": f"Anthropic Judge 실패로 Rule Judge를 사용했습니다: {exc}"}
