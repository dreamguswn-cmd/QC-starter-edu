"""Prometheus 지표 정의 — 문서 기준 메트릭명 사용.

수집 지표
----------
agent_request_total      : 전체 요청 수 (mode × status 레이블)
agent_success_total      : 성공 요청 수
agent_error_total        : 오류 요청 수
agent_response_seconds   : 응답시간 히스토그램 (p95 계산용)
agent_service_status     : 서비스 상태 (1=정상, 0=비정상)
quality_eval_pass_total  : 품질평가 PASS 누적
quality_eval_fail_total  : 품질평가 FAIL 누적
judge_average_score      : Judge 4개 지표 평균 분포
"""
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# ── 요청 지표 ──────────────────────────────────────────────────
AGENT_REQUEST_TOTAL = Counter(
    "agent_request_total",
    "AI Agent 전체 요청 수",
    ["mode", "status"],
)
AGENT_SUCCESS_TOTAL = Counter(
    "agent_success_total",
    "AI Agent 성공 요청 수",
    ["mode"],
)
AGENT_ERROR_TOTAL = Counter(
    "agent_error_total",
    "AI Agent 오류 요청 수",
    ["mode"],
)

# ── 응답시간 (p95 계산용 히스토그램) ──────────────────────────
AGENT_RESPONSE_SECONDS = Histogram(
    "agent_response_seconds",
    "AI Agent 응답시간(초) — p95 모니터링 핵심 지표",
    ["mode"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10],
)

# ── 서비스 상태 (1=정상, 0=비정상) ───────────────────────────
AGENT_SERVICE_STATUS = Gauge(
    "agent_service_status",
    "AI Agent 서비스 상태 (1=정상, 0=비정상)",
)
AGENT_SERVICE_STATUS.set(1)   # 서버 시작 시 정상으로 초기화

# ── 품질평가 지표 ──────────────────────────────────────────────
EVAL_PASS = Counter("quality_eval_pass_total", "품질평가 PASS 누적", ["mode"])
EVAL_FAIL = Counter("quality_eval_fail_total", "품질평가 FAIL 누적", ["mode"])
JUDGE_SCORE = Histogram(
    "judge_average_score",
    "Judge 4개 지표 평균 점수 분포",
    buckets=[1, 2, 3, 4, 4.5, 5],
)


def metrics_response():
    return generate_latest(), CONTENT_TYPE_LATEST
