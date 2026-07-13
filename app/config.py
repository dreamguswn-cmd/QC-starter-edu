import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
QUALITY_DIR = BASE_DIR / "quality"
REPORTS_DIR = QUALITY_DIR / "reports"

load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-4o-mini")

TEST_CASES_PATH = QUALITY_DIR / "test_cases.json"
EVALUATION_JSON_PATH = REPORTS_DIR / "evaluation_result.json"
EVALUATION_CSV_PATH = REPORTS_DIR / "evaluation_result.csv"
FINAL_REPORT_PATH = REPORTS_DIR / "final_quality_report.md"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
