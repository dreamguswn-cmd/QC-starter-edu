import pytest

from quality_diagnosis.three_axis_validation import VALIDATION_CASES, run_validation_case
from utils.pipeline import analyze_voc


@pytest.mark.parametrize("case", VALIDATION_CASES, ids=lambda case: case["id"])
def test_validation_case_is_safe(case):
    outcome = run_validation_case(case, use_independent_judge=False)
    assert outcome["result"]["final"] is not None
    assert len(outcome["result"]["steps"]) == 6
    assert not outcome["error"]


def test_pii_is_masked_before_pipeline_output():
    output = analyze_voc("전화번호 010-1234-5678, test@example.com으로 연락하고 환불해 주세요")
    serialized = str(output)
    assert "010-1234-5678" not in serialized
    assert "test@example.com" not in serialized
    assert "[전화번호]" in serialized
    assert "[이메일]" in serialized


def test_praise_is_not_classified_as_complaint():
    outcome = run_validation_case(next(case for case in VALIDATION_CASES if case.get("praise")))
    interpreted = outcome["result"]["steps"][0]["output"]
    assert interpreted["is_praise"] is True
    assert interpreted["category"] == "칭찬"


def test_risk_expression_is_flagged_without_failure():
    outcome = run_validation_case(next(case for case in VALIDATION_CASES if case.get("risk")))
    interpreted = outcome["result"]["steps"][0]["output"]
    assert interpreted["requires_careful_response"] is True
    assert outcome["result"]["final"] is not None
