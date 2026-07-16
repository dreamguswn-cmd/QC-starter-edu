from __future__ import annotations

import pytest

from quality_diagnosis.qa_test_utils import load_cases, run_case


# Streamlit QA 화면과 동일하게 test_cases.json의 전체 케이스를 실행한다.
CASES = load_cases()


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["case_id"])
def test_pipeline_quality_judgement(case: dict) -> None:
    """Streamlit에 표시되는 케이스별 품질 PASS/FAIL을 pytest에도 그대로 반영한다."""
    out = run_case(case, use_llm=False)

    # 파이프라인 구조 검증
    assert out["result"]["final"] is not None, "최종 결과가 생성되지 않았습니다."
    assert len(out["result"]["steps"]) == 6, "6개 Agent가 모두 실행되지 않았습니다."

    # Streamlit과 동일한 Rule Judge 판정을 pytest 결과로 사용한다.
    judge = out["judge"]
    assert judge["pass"], (
        f"{case['case_id']} 품질 판정 FAIL | "
        f"score={judge.get('score')} | "
        f"reason={judge.get('reason')} | "
        f"critical={out.get('critical_failure', False)}"
    )
