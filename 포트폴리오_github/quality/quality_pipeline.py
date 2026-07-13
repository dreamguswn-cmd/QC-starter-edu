"""품질평가 파이프라인 — 1차 main.py의 케이스 루프를 재사용 가능한 함수로 분리."""
import json

from app.config import TEST_CASES_PATH
from app.judge_agent import evaluate
from app.service_agent import get_answer, get_answer_api
from quality.rule_validator import validate


def load_cases() -> list:
    with open(TEST_CASES_PATH, encoding="utf-8") as f:
        return json.load(f)


def _generate(question: str, mode: str) -> str:
    return get_answer_api(question) if mode == "api" else get_answer(question)


def evaluate_single(question: str, mode: str = "rule", case: dict | None = None) -> dict:
    """질문 1건: 답변 생성 → 규칙 검증 → Judge 평가.

    case가 주어지면 케이스의 기대 키워드/정책을 사용하고,
    운영 트래픽처럼 케이스가 없으면 키워드 검증은 생략(SKIP) 처리한다.
    """
    answer = _generate(question, mode)

    if case:
        rule = validate(answer, case["expected_keyword"])
        expected_policy = case["expected_policy"]
        category = case["category"]
    else:
        rule = {
            "keyword_found": None,
            "rule_status": "SKIP",
            "rule_reason": "기대 키워드가 정의되지 않은 운영 질문입니다.",
        }
        expected_policy = "기준 정보에 근거해 정확하고 안전하게 답변한다."
        category = "운영"

    judged = evaluate(question, answer, expected_policy, category, rule["rule_status"])

    return {
        "case_id": case["case_id"] if case else "LIVE",
        "category": category,
        "test_type": case["test_type"] if case else "Live",
        "user_question": question,
        "mode": mode,
        "ai_answer": answer,
        "rule_validation": rule,
        "evaluation_result": judged,
    }


def run_pipeline(mode: str = "rule") -> list:
    """전체 테스트 케이스 회귀 실행."""
    results = []
    for case in load_cases():
        results.append(evaluate_single(case["user_question"], mode, case))
    return results


if __name__ == "__main__":
    rows = run_pipeline(mode="rule")
    passed = sum(1 for r in rows if r["evaluation_result"]["overall_decision"] == "PASS")
    print(f"완료: {passed}/{len(rows)} PASS")
