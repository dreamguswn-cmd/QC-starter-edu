"""AI Agent 품질관리·운영 모니터링 플랫폼 — FastAPI 서버.

엔드포인트
- GET  /health        서버 상태
- POST /ask           질문 → 답변 (rule | api)
- POST /evaluate      답변 생성 + 규칙 검증 + Judge 평가 1건
- POST /pipeline/run  전체 테스트 케이스 회귀 실행
- GET  /metrics       Prometheus 지표
- GET  /fault-lab     장애 실습(정상·지연·500·타임아웃 시나리오 재현)
"""
import sys
import time
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException, Response

from app import metrics
from app.fault_lab import run_fault_scenario
from app.logger_config import setup_logger
from app.schemas import AskRequest, AskResponse, EvaluateResponse
from app.service_agent import get_answer, get_answer_api

logger = setup_logger()

app = FastAPI(
    title="AI Agent Quality & Monitoring Platform",
    description="AI 챗봇 품질평가 자동화 프로젝트의 운영 확장판",
    version="2.0.0",
)


def _generate(question: str, mode: str) -> str:
    if mode == "api":
        return get_answer_api(question)
    return get_answer(question)


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-agent-quality", "version": "2.0.0"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    start = time.perf_counter()
    try:
        answer = _generate(req.question, req.mode)
        status = "success"
    except RuntimeError as exc:
        # 오류 지표 업데이트
        metrics.AGENT_REQUEST_TOTAL.labels(mode=req.mode, status="error").inc()
        metrics.AGENT_ERROR_TOTAL.labels(mode=req.mode).inc()
        metrics.AGENT_SERVICE_STATUS.set(0)
        logger.error(f"/ask 실패 mode={req.mode} err={exc}")
        raise HTTPException(status_code=503, detail=str(exc))

    elapsed = time.perf_counter() - start

    # 성공 지표 업데이트
    metrics.AGENT_REQUEST_TOTAL.labels(mode=req.mode, status=status).inc()
    metrics.AGENT_SUCCESS_TOTAL.labels(mode=req.mode).inc()
    metrics.AGENT_RESPONSE_SECONDS.labels(mode=req.mode).observe(elapsed)
    metrics.AGENT_SERVICE_STATUS.set(1)
    logger.info(f"/ask mode={req.mode} elapsed={elapsed*1000:.1f}ms q={req.question[:30]!r}")

    return AskResponse(
        question=req.question,
        answer=answer,
        mode=req.mode,
        elapsed_ms=round(elapsed * 1000, 1),
    )


@app.post("/evaluate", response_model=EvaluateResponse)
def evaluate_one(req: AskRequest):
    """운영 중 답변 1건을 즉시 평가한다 (규칙 검증 + Judge)."""
    from quality.quality_pipeline import evaluate_single

    start = time.perf_counter()
    try:
        result = evaluate_single(req.question, req.mode)
    except RuntimeError as exc:
        metrics.AGENT_ERROR_TOTAL.labels(mode=req.mode).inc()
        raise HTTPException(status_code=503, detail=str(exc))
    elapsed = time.perf_counter() - start

    decision = result["evaluation_result"]["overall_decision"]
    if decision == "PASS":
        metrics.EVAL_PASS.labels(mode=req.mode).inc()
    else:
        metrics.EVAL_FAIL.labels(mode=req.mode).inc()

    scores = {
        k: result["evaluation_result"][k]["score"]
        for k in ("accuracy", "groundedness", "helpfulness", "safety")
    }
    metrics.JUDGE_SCORE.observe(sum(scores.values()) / 4)
    metrics.AGENT_RESPONSE_SECONDS.labels(mode=req.mode).observe(elapsed)
    logger.info(f"/evaluate mode={req.mode} decision={decision} scores={scores}")

    return EvaluateResponse(
        question=req.question,
        answer=result["ai_answer"],
        mode=req.mode,
        rule_status=result["rule_validation"]["rule_status"],
        overall_decision=decision,
        scores=scores,
        summary=result["evaluation_result"]["summary"],
        elapsed_ms=round(elapsed * 1000, 1),
    )


@app.post("/pipeline/run")
def run_pipeline_endpoint(mode: str = "rule"):
    """quality/test_cases.json 전체를 회귀 실행하고 요약을 반환한다."""
    from quality.quality_pipeline import run_pipeline
    from quality.report_generator import generate_reports

    if mode not in ("rule", "api"):
        raise HTTPException(status_code=422, detail="mode는 rule 또는 api")
    try:
        results = run_pipeline(mode=mode)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    generate_reports(results)

    total = len(results)
    passed = sum(
        1 for r in results if r["evaluation_result"]["overall_decision"] == "PASS"
    )
    for r in results:
        if r["evaluation_result"]["overall_decision"] == "PASS":
            metrics.EVAL_PASS.labels(mode=mode).inc()
        else:
            metrics.EVAL_FAIL.labels(mode=mode).inc()
    logger.info(f"/pipeline/run mode={mode} pass={passed}/{total}")
    return {
        "mode": mode,
        "total": total,
        "pass": passed,
        "fail": total - passed,
        "pass_rate": round(passed / total * 100, 1) if total else 0.0,
        "reports_dir": "quality/reports/",
    }


@app.get("/fault-lab")
def fault_lab(scenario: str = "normal", delay_seconds: float = 3.0):
    """장애 실습용 엔드포인트 — normal · delay · error500 · timeout 시나리오를 의도적으로 재현한다."""
    logger.info(f"/fault-lab scenario={scenario} delay_seconds={delay_seconds}")
    start = time.perf_counter()
    try:
        result = run_fault_scenario(scenario, delay_seconds)
    except HTTPException:
        elapsed = time.perf_counter() - start
        metrics.AGENT_REQUEST_TOTAL.labels(mode="fault-lab", status="error").inc()
        metrics.AGENT_ERROR_TOTAL.labels(mode="fault-lab").inc()
        metrics.AGENT_RESPONSE_SECONDS.labels(mode="fault-lab").observe(elapsed)
        raise

    elapsed = time.perf_counter() - start
    metrics.AGENT_REQUEST_TOTAL.labels(mode="fault-lab", status="success").inc()
    metrics.AGENT_SUCCESS_TOTAL.labels(mode="fault-lab").inc()
    metrics.AGENT_RESPONSE_SECONDS.labels(mode="fault-lab").observe(elapsed)
    return result


@app.get("/metrics")
def metrics_endpoint():
    payload, content_type = metrics.metrics_response()
    return Response(content=payload, media_type=content_type)
