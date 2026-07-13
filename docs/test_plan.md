# 테스트 계획서

## 1. 목적
AI Agent(교육과정 안내 챗봇)의 기능·품질·성능·운영 관측 가능성을 6개 수준으로 검증한다.

## 2. 테스트 수준과 합격 기준
| 수준 | 항목 | 방법 | 합격 기준 |
| --- | --- | --- | --- |
| 1 | Health | pytest `tests/test_health.py` | /health 200 + /metrics 노출 |
| 2 | API | pytest `tests/test_agent_api.py` | Happy 4케이스 키워드 포함, 응답 스키마 일치 |
| 3 | Quality Pipeline | pytest `tests/test_quality_pipeline.py` | 7케이스 실행·rule 모드 7/7 PASS·보고서 3종 생성 |
| 4 | Negative | pytest `tests/test_negative_cases.py` | 빈 질문/잘못된 mode/초과 길이 422, 위험 질문 거절, 범위 외 안내 |
| 5 | Performance | k6 `performance/k6_test.js` | 오류율 5% 이하 AND p95 1000ms 이하 |
| 6 | Monitoring | Prometheus/Grafana | 요청량·오류율·p95·PASS율 4개 지표 실시간 관측 |

## 3. 테스트 데이터
`quality/test_cases.json` — Happy 4 / Edge 2 / Negative 1 (1차 프로젝트 검증 완료 세트 승계)

## 4. 실행 결과 (2026-07-06 기준)
- pytest: **15 passed / 0 failed** (수준 1~4)
- 파이프라인 rule 모드: 7/7 PASS (기준선)
- 성능·모니터링: 별도 보고서 참조 (performance_report.md)
