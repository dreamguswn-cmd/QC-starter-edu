"""품질 평가 결과를 JSON·CSV·Markdown 보고서로 저장한다."""
import csv
import datetime
import json

from app.config import (
    EVALUATION_CSV_PATH,
    EVALUATION_JSON_PATH,
    FINAL_REPORT_PATH,
    REPORTS_DIR,
)

SCORE_KEYS = ("accuracy", "groundedness", "helpfulness", "safety")


def _flatten(result: dict) -> dict:
    ev = result["evaluation_result"]
    rv = result["rule_validation"]
    return {
        "case_id": result["case_id"],
        "category": result["category"],
        "test_type": result["test_type"],
        "user_question": result["user_question"],
        "mode": result["mode"],
        "ai_answer": result["ai_answer"],
        "keyword_found": rv.get("keyword_found"),
        "rule_status": rv.get("rule_status"),
        "accuracy_score": ev["accuracy"]["score"],
        "groundedness_score": ev["groundedness"]["score"],
        "helpfulness_score": ev["helpfulness"]["score"],
        "safety_score": ev["safety"]["score"],
        "overall_decision": ev["overall_decision"],
        "summary": ev["summary"],
    }


def generate_reports(results: list) -> None:
    """JSON / CSV / Markdown 보고서를 quality/reports/ 에 저장한다."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # JSON
    EVALUATION_JSON_PATH.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # CSV
    rows = [_flatten(r) for r in results]
    if rows:
        with open(EVALUATION_CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    # Markdown
    total = len(rows)
    passed = sum(1 for r in rows if r["overall_decision"] == "PASS")
    failed = total - passed
    pass_rate = round(passed / total * 100, 1) if total else 0.0
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# AI Agent 품질평가 최종 보고서",
        "",
        f"- 생성 시각: {now}",
        f"- 총 케이스: {total}건 / PASS {passed}건 / FAIL {failed}건 / 통과율 {pass_rate}%",
        "",
        "## 케이스별 결과",
        "",
        "| case_id | category | 판정 | 정확성 | 근거성 | 유용성 | 안전성 | 요약 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        lines.append(
            f"| {r['case_id']} | {r['category']} | {r['overall_decision']} "
            f"| {r['accuracy_score']} | {r['groundedness_score']} "
            f"| {r['helpfulness_score']} | {r['safety_score']} | {r['summary']} |"
        )

    fail_rows = [r for r in rows if r["overall_decision"] == "FAIL"]
    if fail_rows:
        lines += ["", "## FAIL 케이스 상세", ""]
        for r in fail_rows:
            lines += [
                f"### {r['case_id']} — {r['category']}",
                f"- **질문:** {r['user_question']}",
                f"- **AI 답변:** {r['ai_answer']}",
                f"- **규칙 검증:** {r['rule_status']}",
                f"- **요약:** {r['summary']}",
                "",
            ]

    FINAL_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
