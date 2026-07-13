# AI Agent 품질관리 플랫폼 — 단계별 실행 가이드

> **방금 만든 파일 기준** | Python 3.10+ | 로컬 실행 중심
> `tests/` 폴더 기준 pytest **25 passed** 확인 완료 (2026-07)

---

## [현재 상태] Docker로 이미 실행 중이라면 (2026-07-08 기준)

이 문서의 1~7단계는 **Docker 없이 로컬에서** 직접 실행하는 경우를 기준으로 작성되어 있습니다.
지금처럼 **Docker Desktop이 이미 떠 있고 `docker compose up`으로 실행한 상태**라면, 아래 순서를 따르면 됩니다 (1~7단계의 로컬 명령어는 필요 없음 — 컨테이너가 이미 그 역할을 대신함).

### 지금 실행 중인 스택
```
portfolio/docker-compose.yml 기준
app         → http://localhost:8000/docs   (FastAPI, health/ask/metrics/fault-lab)
prometheus  → http://localhost:9090        (targets: app:8000, health = up 확인됨)
grafana     → http://localhost:3000        (admin / admin)
```

### 다음에 할 일 (순서대로)

1. **app이 정상인지 확인**
   ```bash
   curl http://localhost:8000/health
   # {"status":"ok","service":"ai-agent-quality","version":"2.0.0"}
   ```

2. **Prometheus가 app을 잘 긁어가는지 확인**
   - 브라우저: http://localhost:9090/targets
   - `ai-agent-quality` job이 **State = UP** 이어야 정상 (컨테이너 간 네트워크가 `app:8000`으로 통신하기 때문에, 로컬 uvicorn 대신 이 컨테이너가 지표를 만들어야 함)

3. **Grafana에 데이터소스 연결** (최초 1회만)
   - http://localhost:3000 접속 → `admin` / `admin` 로그인
   - 왼쪽 메뉴 Connections → Data Sources → Add data source → Prometheus 선택
   - URL: `http://prometheus:9090` (컨테이너 이름으로 입력 — `localhost` 아님)
   - Save & Test → 성공 메시지 확인

4. **대시보드 불러오기**
   - Dashboards → New → Import
   - `monitoring/grafana_dashboard.json` 파일 업로드 (또는 내용 붙여넣기)
   - 방금 만든 Prometheus 데이터소스 선택 → Import

5. **지표를 쌓기 위해 트래픽 발생시키기** (그래프가 비어있으면 이 단계가 안 된 것)
   ```bash
   curl -X POST http://localhost:8000/ask \
     -H "Content-Type: application/json" \
     -d '{"question":"총 교육시간은?","mode":"rule"}'

   curl -X POST "http://localhost:8000/pipeline/run?mode=rule"
   ```
   실행 후 Grafana 대시보드 새로고침 → 그래프에 값이 찍히는지 확인

6. **끝낼 때**
   ```bash
   cd portfolio
   docker compose down        # 컨테이너만 정리 (이미지는 남음)
   docker compose down -v     # 볼륨까지 완전히 정리하고 싶을 때
   ```

> 참고: 위 실행 과정에서 겪은 포트 충돌 문제와 해결 방법은 [defect_report.md의 DEF-005](defect_report.md)에 기록해 두었습니다.

---

## 사전 준비 (공통)

```bash
# 1. 프로젝트 루트로 이동
cd ai_agent_quality_portfolio

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 OPENAI_API_KEY= 에 키 입력
# ※ 키 없이도 rule 모드는 전부 동작함
```

---

## 1단계 — Service Agent + FastAPI 서버 기동

**목적:** `/health`, `/ask`, `/metrics` API가 정상 동작하는지 확인

```bash
# 서버 실행 (터미널 1 — 계속 켜두기)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 뜨면 브라우저에서 확인:

```
http://localhost:8000/docs       → Swagger UI (직접 API 실행 가능)
http://localhost:8000/health     → {"status":"ok",...}
http://localhost:8000/metrics    → Prometheus 텍스트 포맷 지표
```

터미널에서 직접 호출 테스트:

```bash
# 교육시간 질문 (rule 모드)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "이 과정은 총 몇 시간인가요?", "mode": "rule"}'

# 예상 응답
# {"question":"...","answer":"...총 320시간...","mode":"rule","elapsed_ms":0.x}
```

**핵심 파일:** `app/main.py` · `app/service_agent.py` · `app/knowledge_base.py`

---

## 2단계 — pytest 기능 테스트 (수준 1~4 전체)

**목적:** Health · API · 품질 파이프라인 · Negative 케이스 25건 자동 검증

```bash
# 전체 테스트 실행 (서버 없이 동작 — TestClient 사용)
pytest tests/ -v

# 수준별로 개별 실행
pytest tests/test_health.py -v          # 수준 1: Health (3건)
pytest tests/test_agent_api.py -v       # 수준 2: API (5건)
pytest tests/test_quality_pipeline.py -v # 수준 3: Pipeline (9건)
pytest tests/test_negative_cases.py -v  # 수준 4: Negative (8건)

# 커버리지 리포트 포함
pytest tests/ -v --cov=app --cov=quality --cov-report=term-missing
```

**기대 결과:**
```
25 passed, 0 failed
수준1(Health) 3/3 · 수준2(API) 5/5 · 수준3(Pipeline) 9/9 · 수준4(Negative) 8/8
```

**핵심 파일:** `tests/test_health.py` · `tests/test_agent_api.py`
             `tests/test_quality_pipeline.py` · `tests/test_negative_cases.py`

---

## 3단계 — AI Judge 품질평가 실행

**목적:** Judge Agent가 정확성·근거성·유용성·안전성 4개 지표로 답변을 평가

```bash
# 파이프라인 CLI 직접 실행 (rule 모드)
python -m quality.quality_pipeline

# 예상 출력
# 완료: 7/10 PASS  (FAIL: 3건)
```

Python 코드로 개별 케이스 평가:

```python
# 터미널에서 python 실행 후
import sys; sys.path.insert(0, '.')
from quality.quality_pipeline import evaluate_single

result = evaluate_single(
    question="이 과정은 총 몇 시간인가요?",
    mode="rule"
)
print(result["evaluation_result"])
# {'accuracy': {'score': 5, ...}, 'overall_decision': 'PASS', ...}
```

**핵심 파일:** `app/judge_agent.py` · `quality/quality_pipeline.py` · `quality/rule_validator.py`

---

## 4단계 — JSON·CSV·Markdown 보고서 생성

**목적:** 평가 결과를 3가지 형식으로 `quality/reports/` 에 자동 저장

```bash
# 파이프라인 실행 → 보고서 자동 생성
python -m quality.quality_pipeline
```

생성되는 파일:

```
quality/reports/
├─ evaluation_result.json    ← 원본 전체 데이터 (10건)
├─ evaluation_result.csv     ← Streamlit 대시보드 입력 데이터
└─ final_quality_report.md   ← 케이스별 결과 + FAIL 상세 Markdown 보고서
```

Python에서 직접 호출:

```python
import sys; sys.path.insert(0, '.')
from quality.quality_pipeline import run_pipeline
from quality.report_generator import generate_reports

results = run_pipeline(mode="rule")
generate_reports(results)
print("보고서 생성 완료 → quality/reports/")
```

FastAPI 엔드포인트로도 실행 가능 (서버 기동 후):

```bash
curl -X POST "http://localhost:8000/pipeline/run?mode=rule"
# {"mode":"rule","total":10,"pass":7,"fail":3,"pass_rate":70.0,...}
```

**핵심 파일:** `quality/report_generator.py`

---

## 5단계 — Streamlit 품질 대시보드 실행

**목적:** 평가 결과를 KPI 카드·차트·FAIL 상세 테이블로 시각화

**사전 조건:** 4단계 실행 후 `quality/reports/evaluation_result.csv` 존재해야 함

```bash
# 대시보드 실행 (터미널 2)
streamlit run dashboard/streamlit_app.py
```

브라우저 자동 오픈: `http://localhost:8501`

화면 구성:
```
상단 KPI   : 총 10건 · PASS 7 · FAIL 3 · 통과율 70% · 평균점수
케이스 테이블: 색상 배지(🟢🟡🟠🔴)로 점수 표시 + ✅/❌ 판정
좌측 차트  : 카테고리별 통과율(%)
우측 차트  : 정확성·근거성·유용성·안전성 평균 점수
FAIL 상세  : TC-008~010 질문·답변·점수·사유 펼침 표시
```

**핵심 파일:** `dashboard/streamlit_app.py`

---

## 6단계 — k6 성능 테스트

**목적:** 30 VU 동시 접속 환경에서 오류율·응답시간 측정

**사전 조건:** 1단계 서버 실행 중 + k6 설치 (`brew install k6` 또는 공식 설치)

```bash
# rule 모드 성능 테스트
k6 run performance/k6_test.js

# api 모드 성능 테스트 (OPENAI_API_KEY 필요)
MODE=api k6 run performance/k6_test.js
```

**부하 시나리오:**
```
0→30s: VU 0→10 (워밍업)
30→90s: VU 10→30 유지 (부하)
90→120s: VU 30→0 (정리)
```

**합격 기준:**
```
✅ 오류율(http_req_failed) < 5%
✅ p95 응답시간(http_req_duration) < 1000ms
```

**핵심 파일:** `performance/k6_test.js`

---

## 7단계 — Prometheus 지표 수집

**목적:** FastAPI `/metrics`에서 운영 지표를 실시간 Pull 방식으로 수집

**Docker 환경 기준 (권장):**

```bash
docker compose up --build
# Prometheus: http://localhost:9090
```

**로컬 단독 실행 (Docker 없이):**

```bash
# 1. 서버 기동 (1단계)
uvicorn app.main:app --reload --port 8000

# 2. /metrics 직접 확인
curl http://localhost:8000/metrics | grep ask_requests_total
curl http://localhost:8000/metrics | grep quality_eval_pass_total

# 3. 서버에 요청 발생시키기 (지표 쌓기)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"총 교육시간은?","mode":"rule"}'

curl -X POST "http://localhost:8000/pipeline/run?mode=rule"

# 4. 다시 /metrics 확인 → 카운터 증가 확인
curl http://localhost:8000/metrics | grep "ask_requests_total\|quality_eval"
```

수집되는 지표:
```
ask_requests_total{mode,status}     → /ask 호출 수 (mode×status 레이블)
ask_latency_seconds{mode}           → /ask 응답시간 히스토그램
quality_eval_pass_total{mode}       → PASS 누적 수
quality_eval_fail_total{mode}       → FAIL 누적 수
judge_average_score                 → Judge 4개 지표 평균 분포
```

**핵심 파일:** `app/metrics.py` · `monitoring/prometheus.yml`

---

## 8단계 — Grafana 운영 대시보드

**목적:** Prometheus 메트릭을 실시간 그래프로 시각화

```bash
# Docker Compose로 전체 스택 실행
docker compose up --build
```

```
서비스               포트    접속 정보
app (FastAPI)        8000    http://localhost:8000/docs
Prometheus           9090    http://localhost:9090
Grafana              3000    http://localhost:3000  (admin / admin)
```

Grafana 설정 순서:
```
1. http://localhost:3000 접속 (admin/admin)
2. Connections → Data Sources → Add → Prometheus
   URL: http://prometheus:9090
3. Dashboards → Import → monitoring/grafana_dashboard.json 업로드
```

주요 패널 PromQL:
```promql
# p95 응답시간
histogram_quantile(0.95, sum(rate(ask_latency_seconds_bucket[5m])) by (le))

# 분당 요청 수
rate(ask_requests_total[1m])

# PASS율
quality_eval_pass_total / (quality_eval_pass_total + quality_eval_fail_total)
```

**핵심 파일:** `monitoring/prometheus.yml` · `monitoring/grafana_dashboard.json`

---

## 9단계 — Jira 결함 관리

**목적:** FAIL 케이스를 Jira에 등록해 결함 추적 관리

Streamlit 대시보드(5단계)에서 FAIL 케이스 상세 정보를 확인 후 Jira에 등록:

```
[Jira 등록 정보 예시 — TC-009]
프로젝트  : WT4 (AI QA 포트폴리오)
이슈 유형 : Bug
제목      : [TC-009] 수료 증서 수령 시기 질문에 수료 기준 답변 반환
심각도    : Medium
재현 절차 :
  1. POST /ask {"question":"수료 증서는 언제 받나요?","mode":"rule"}
  2. 응답 확인
기대 결과 : "확인할 수 없습니다" 안내
실제 결과 : 수료 기준(80%) 답변 반환
근거      : evaluation_result.csv TC-009 참조
조치 계획 : knowledge_base.py UNKNOWN_ANSWER 조건 키워드 보완
```

등록 절차 (간략):
```
1. Streamlit ❌ FAIL 상세 expander에서 case_id·질문·답변·요약 확인
2. Jira → 새 Bug 등록 (재현 절차 + 기대/실제 결과 명시)
3. knowledge_base.py 또는 service_agent.py 수정
4. pytest tests/ -v 재실행 → GREEN 확인 후 Close
```

참고 문서: `docs/defect_report.md`

---

## 10단계 — Docker 통합 실행 (전체 환경 재현)

**목적:** 로컬 Python 환경 없이도 전체 스택을 단일 명령으로 재현

```bash
# 전체 빌드 & 실행
docker compose up --build

# 백그라운드 실행
docker compose up --build -d

# 로그 확인
docker compose logs -f app

# 파이프라인 실행 (컨테이너 내부)
docker compose exec app python -m quality.quality_pipeline

# pytest 실행 (컨테이너 내부)
docker compose exec app pytest tests/ -v

# 전체 종료
docker compose down
```

**docker-compose.yml 서비스 구성:**
```
app         → FastAPI (포트 8000) + quality/reports 볼륨 마운트
prometheus  → Prometheus (포트 9090) + prometheus.yml 마운트
grafana     → Grafana (포트 3000) + admin/admin
```

---

## 전체 실행 흐름 요약

```
[사전 준비]
pip install -r requirements.txt
cp .env.example .env

      ↓ 1단계
uvicorn app.main:app --reload
      ↓ 2단계
pytest tests/ -v                          → 25 passed
      ↓ 3단계
python -m quality.quality_pipeline        → 7/10 PASS · 3 FAIL 확인
      ↓ 4단계 (자동 생성)
quality/reports/evaluation_result.csv
quality/reports/evaluation_result.json
quality/reports/final_quality_report.md
      ↓ 5단계
streamlit run dashboard/streamlit_app.py  → http://localhost:8501
      ↓ 6단계
k6 run performance/k6_test.js             → 오류율 0% · p95 <1000ms
      ↓ 7단계 (서버 실행 중 자동)
http://localhost:8000/metrics             → Prometheus Pull
      ↓ 8단계
docker compose up → Grafana http://localhost:3000
      ↓ 9단계
Streamlit FAIL 상세 → Jira Bug 등록 → 수정 → pytest GREEN
      ↓ 10단계
docker compose up --build                 → 전체 환경 재현 완료
```

---

## 파일-단계 대응표

| 단계 | 실행 명령 | 핵심 파일 |
|------|-----------|-----------|
| 1 | `uvicorn app.main:app --reload` | `app/main.py`, `app/service_agent.py`, `app/knowledge_base.py` |
| 2 | `pytest tests/ -v` | `tests/test_health.py`, `tests/test_agent_api.py`, `tests/test_quality_pipeline.py`, `tests/test_negative_cases.py` |
| 3 | `python -m quality.quality_pipeline` | `app/judge_agent.py`, `quality/quality_pipeline.py`, `quality/rule_validator.py` |
| 4 | *(3단계 실행 시 자동)* | `quality/report_generator.py` |
| 5 | `streamlit run dashboard/streamlit_app.py` | `dashboard/streamlit_app.py` |
| 6 | `k6 run performance/k6_test.js` | `performance/k6_test.js` |
| 7 | `curl http://localhost:8000/metrics` | `app/metrics.py`, `monitoring/prometheus.yml` |
| 8 | `docker compose up` | `monitoring/grafana_dashboard.json`, `docker-compose.yml` |
| 9 | Streamlit → Jira 수동 등록 | `docs/defect_report.md` |
| 10 | `docker compose up --build` | `Dockerfile`, `docker-compose.yml` |
