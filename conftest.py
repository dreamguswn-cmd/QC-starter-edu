"""pytest 세션 종료 시 기능 테스트 판정 결과를 quality/reports/pytest_test_report.md 로 기록한다."""
import ast
import datetime
from pathlib import Path

from app.config import REPORTS_DIR

PYTEST_REPORT_PATH = REPORTS_DIR / "pytest_test_report.md"

_results: list[dict] = []
_level_cache: dict[str, str] = {}


def _level_label(file_path: str) -> str:
    if file_path not in _level_cache:
        try:
            tree = ast.parse(Path(file_path).read_text(encoding="utf-8"))
            doc = (ast.get_docstring(tree) or "").strip().splitlines()
            _level_cache[file_path] = doc[0] if doc else Path(file_path).name
        except OSError:
            _level_cache[file_path] = Path(file_path).name
    return _level_cache[file_path]


def pytest_runtest_logreport(report):
    if report.when == "setup" and report.failed:
        outcome = "ERROR"
    elif report.when == "setup" and report.skipped:
        outcome = "SKIP"
    elif report.when == "call":
        outcome = "PASS" if report.passed else "FAIL"
    else:
        return

    file_path = report.location[0]
    test_name = report.nodeid.split("::", 1)[1]
    try:
        test_name = test_name.encode("ascii").decode("unicode_escape")
    except (UnicodeError, ValueError):
        pass
    _results.append(
        {
            "level": _level_label(file_path),
            "file": Path(file_path).name,
            "test": test_name,
            "outcome": outcome,
            "duration_ms": round(report.duration * 1000, 1),
        }
    )


def pytest_sessionfinish(session, exitstatus):
    if not _results:
        return

    total = len(_results)
    passed = sum(1 for r in _results if r["outcome"] == "PASS")
    failed = sum(1 for r in _results if r["outcome"] in ("FAIL", "ERROR"))
    skipped = sum(1 for r in _results if r["outcome"] == "SKIP")
    pass_rate = round(passed / total * 100, 1) if total else 0.0

    lines = [
        "# pytest 기능 테스트 판정 결과표",
        "",
        f"- 생성 시각: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}",
        f"- 총 테스트: {total}건 / PASS {passed}건 / FAIL {failed}건 / SKIP {skipped}건",
        f"- 통과율: {pass_rate}%",
        "",
        "| 테스트 수준 | 파일 | 테스트 | 판정 | 소요(ms) |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in _results:
        lines.append(
            f"| {r['level']} | {r['file']} | {r['test']} | {r['outcome']} | {r['duration_ms']} |"
        )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    PYTEST_REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
