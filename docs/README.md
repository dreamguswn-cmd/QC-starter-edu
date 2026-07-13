# AI Agent 품질관리·운영 모니터링 플랫폼 (ai_agent_quality_portfolio)

1차 프로젝트 `ai_quality_final_project`(AI 챗봇 품질평가 자동화)를
**개발 → 테스트 → 품질평가 → 성능검증 → 모니터링 → 배포 → 문서화** 전체 흐름을 갖춘
운영 플랫폼으로 확장한 4조 포트폴리오입니다.

## 구조
```
app/         → FastAPI AI Agent API 서비스 (/health, /ask, /evaluate, /pipeline/run, /metrics)
quality/     → 규칙 검증·품질 파이프라인·보고서 생성
tests/       → pytest 자동 테스트 (Health / API / Pipeline / Negative — 15 tests)
performance/ → k6 부하 테스트
monitoring/  → Prometheus 설정 · Grafana 대시보드 JSON
dashboard/   → Streamlit 품질 리포트
docs/        → 테스트 계획서·결함 보고서·성능 보고서·최종 품질 보고서
```

## 실행 방법
### 로컬
```bash
pip install -r requirements.txt
cp .env.example .env            # OPENAI_API_KEY 입력 (없어도 rule 모드는 동작)
uvicorn app.main:app --reload   # http://localhost:8000/docs
pytest -v                       # 자동 테스트 15건
python -m quality.quality_pipeline           # 품질 파이프라인 (CLI)
streamlit run dashboard/streamlit_app.py     # 품질 대시보드
k6 run performance/k6_test.js                # 성능 테스트 (서버 기동 상태에서)
```
### Docker (전체 환경 재현)
```bash
docker compose up --build
# app: :8000 / Prometheus: :9090 / Grafana: :3000 (admin/admin)
```

## API 요약
| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| GET | /health | 서버 상태 |
| POST | /ask | 질문 → 답변 (mode: rule/api) |
| POST | /evaluate | 답변 1건 즉시 평가 (규칙+Judge) |
| POST | /pipeline/run | 전체 케이스 회귀 실행 + 보고서 생성 |
| GET | /metrics | Prometheus 지표 |

## 장애 처리 설계
- 빈 질문·형식 오류 → Pydantic 검증으로 422
- OPENAI_API_KEY 미설정 상태의 api 모드 → 503 (fail-fast)
- Judge 호출 실패 → 규칙 기반 fallback 평가로 파이프라인 지속
