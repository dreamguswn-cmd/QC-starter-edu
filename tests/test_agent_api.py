"""테스트 수준 2 — API Test: POST /ask Happy Path 4케이스 응답 스키마·키워드 검증."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

HAPPY_CASES = [
    ("이 과정은 총 몇 시간인가요?",              "320"),
    ("지각하면 어떻게 처리되나요?",               "지각 3회"),
    ("수료하려면 출석률이 얼마나 되어야 하나요?",  "80퍼센트"),
    ("수료 후 취업 지원은 어떻게 받나요?",        "취업 상담"),
]


def test_ask_response_schema():
    """POST /ask → 응답 스키마(question/answer/mode/elapsed_ms) 확인."""
    res = client.post("/ask", json={"question": "총 교육시간이 몇 시간인가요?", "mode": "rule"})
    assert res.status_code == 200
    body = res.json()
    for field in ("question", "answer", "mode", "elapsed_ms"):
        assert field in body, f"응답에 '{field}' 필드 없음"


def test_ask_happy_case_education_hours():
    """교육시간 질문 → 답변에 '320' 포함."""
    question, keyword = HAPPY_CASES[0]
    res = client.post("/ask", json={"question": question, "mode": "rule"})
    assert res.status_code == 200
    assert keyword in res.json()["answer"]


def test_ask_happy_case_attendance_rule():
    """지각 규정 질문 → 답변에 '지각 3회' 포함."""
    question, keyword = HAPPY_CASES[1]
    res = client.post("/ask", json={"question": question, "mode": "rule"})
    assert res.status_code == 200
    assert keyword in res.json()["answer"]


def test_ask_happy_case_completion_rate():
    """수료 기준 질문 → 답변에 '80퍼센트' 포함."""
    question, keyword = HAPPY_CASES[2]
    res = client.post("/ask", json={"question": question, "mode": "rule"})
    assert res.status_code == 200
    assert keyword in res.json()["answer"]


def test_ask_happy_case_job_support():
    """취업지원 질문 → 답변에 '취업 상담' 포함."""
    question, keyword = HAPPY_CASES[3]
    res = client.post("/ask", json={"question": question, "mode": "rule"})
    assert res.status_code == 200
    assert keyword in res.json()["answer"]
