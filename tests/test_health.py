"""테스트 수준 1 — Health Test: 서버 상태 및 Prometheus 메트릭 노출 확인."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_status_ok():
    """GET /health → 200 + status: ok."""
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"


def test_health_service_name():
    """GET /health → service 필드 포함."""
    res = client.get("/health")
    assert "service" in res.json()


def test_metrics_endpoint_exposed():
    """GET /metrics → 200 + Prometheus 포맷 텍스트 반환."""
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "ask_requests_total" in res.text or "quality_eval" in res.text or "# HELP" in res.text
