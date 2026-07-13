"""장애 실습 엔드포인트(/fault-lab) 테스트 — normal · delay · error500 · timeout 시나리오."""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_normal_response():
    response = client.get(
        "/fault-lab?scenario=normal"
    )

    assert response.status_code == 200
    assert response.json()["scenario"] == "normal"


def test_delay_response():
    start_time = time.time()

    response = client.get(
        "/fault-lab?scenario=delay&delay_seconds=1"
    )

    elapsed_time = time.time() - start_time

    assert response.status_code == 200
    assert response.json()["scenario"] == "delay"
    assert elapsed_time >= 1


def test_error500_response():
    response = client.get(
        "/fault-lab?scenario=error500"
    )

    assert response.status_code == 500


def test_timeout_response():
    response = client.get(
        "/fault-lab?scenario=timeout&delay_seconds=1"
    )

    assert response.status_code == 504
