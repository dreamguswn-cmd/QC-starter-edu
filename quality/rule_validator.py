"""규칙 기반 키워드 검증 — 기대 키워드가 답변에 포함되는지 확인한다."""


def validate(answer: str, expected_keyword: str) -> dict:
    """answer 안에 expected_keyword가 포함되면 PASS, 아니면 FAIL."""
    found = expected_keyword.lower() in answer.lower()
    return {
        "keyword_found": found,
        "rule_status": "PASS" if found else "FAIL",
        "rule_reason": (
            f"기대 키워드 '{expected_keyword}'가 답변에 포함되어 있습니다."
            if found
            else f"기대 키워드 '{expected_keyword}'가 답변에서 발견되지 않았습니다."
        ),
    }
