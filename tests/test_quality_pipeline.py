"""테스트 수준 3 — Quality Pipeline Test: 파이프라인 전체 흐름 + 보고서 3종 생성 확인."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from app.config import (
    EVALUATION_CSV_PATH,
    EVALUATION_JSON_PATH,
    FINAL_REPORT_PATH,
    TEST_CASES_PATH,
)
from quality.quality_pipeline import load_cases, run_pipeline
from quality.report_generator import generate_reports
from quality.rule_validator import validate


# ── 규칙 검증기 단위 테스트 ──────────────────────────────────
def test_rule_validator_pass():
    """기대 키워드가 답변에 포함되면 PASS."""
    result = validate("지각 3회는 결석 1일로 처리됩니다.", "지각 3회")
    assert result["rule_status"] == "PASS"
    assert result["keyword_found"] is True


def test_rule_validator_fail():
    """기대 키워드가 없으면 FAIL."""
    result = validate("죄송합니다, 확인할 수 없습니다.", "지각 3회")
    assert result["rule_status"] == "FAIL"
    assert result["keyword_found"] is False


# ── 테스트케이스 로드 ────────────────────────────────────────
def test_test_cases_json_exists():
    """quality/test_cases.json 파일이 존재해야 한다."""
    assert TEST_CASES_PATH.exists(), "test_cases.json 없음"


def test_test_cases_structure():
    """각 케이스에 필수 필드(case_id, user_question, expected_keyword 등)가 있어야 한다."""
    cases = load_cases()
    assert len(cases) >= 10, f"케이스 수 부족: {len(cases)}건"
    required = {"case_id", "category", "test_type", "user_question",
                "expected_keyword", "expected_policy"}
    for c in cases:
        missing = required - set(c.keys())
        assert not missing, f"{c['case_id']} 필드 누락: {missing}"


# ── 파이프라인 실행 ──────────────────────────────────────────
def test_pipeline_rule_mode_returns_all_cases():
    """run_pipeline(rule)은 test_cases.json의 케이스 수만큼 결과를 반환한다."""
    cases = load_cases()
    results = run_pipeline(mode="rule")
    assert len(results) == len(cases)


def test_pipeline_rule_mode_pass_7():
    """rule 모드 파이프라인: PASS 7건, FAIL 3건이 나와야 한다."""
    results = run_pipeline(mode="rule")
    passed = sum(1 for r in results if r["evaluation_result"]["overall_decision"] == "PASS")
    failed = len(results) - passed
    assert passed == 7, f"PASS 기대 7건, 실제 {passed}건"
    assert failed == 3, f"FAIL 기대 3건, 실제 {failed}건"


def test_pipeline_result_has_required_keys():
    """각 결과에 필수 키(case_id, ai_answer, rule_validation, evaluation_result)가 있어야 한다."""
    results = run_pipeline(mode="rule")
    required = {"case_id", "category", "test_type", "user_question",
                "mode", "ai_answer", "rule_validation", "evaluation_result"}
    for r in results:
        missing = required - set(r.keys())
        assert not missing, f"{r['case_id']} 키 누락: {missing}"


# ── 보고서 생성 확인 ─────────────────────────────────────────
def test_reports_generated():
    """generate_reports 실행 후 JSON·CSV·Markdown 3종 파일이 생성되어야 한다."""
    results = run_pipeline(mode="rule")
    generate_reports(results)
    assert EVALUATION_JSON_PATH.exists(), "evaluation_result.json 없음"
    assert EVALUATION_CSV_PATH.exists(), "evaluation_result.csv 없음"
    assert FINAL_REPORT_PATH.exists(),   "final_quality_report.md 없음"


def test_evaluation_json_valid():
    """생성된 JSON이 파싱 가능하고 10건이어야 한다."""
    results = run_pipeline(mode="rule")
    generate_reports(results)
    data = json.loads(EVALUATION_JSON_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 10
