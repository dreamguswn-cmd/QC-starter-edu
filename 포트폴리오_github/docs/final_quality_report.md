# 최종 품질 보고서

## 1. 요약
| 영역 | 결과 |
| --- | --- |
| 기능 테스트 (pytest) | 15/15 PASS |
| 품질 파이프라인 (rule 기준선) | 7/7 PASS (통과율 100%) |
| Negative/장애 입력 | 빈 질문·형식 오류 422, 위험 질문 거절, 범위 외 안내 — 전부 정상 |
| 성능 (k6) | performance_report.md 기준 기입 |
| 모니터링 | /metrics 노출, Prometheus 수집, Grafana 4패널(요청량·p95·오류율·PASS율) |
| 배포 | docker compose up 1회로 app+Prometheus+Grafana 재현 |

## 2. 판정
- **조건부 운영 가능**: rule 모드는 기능·품질·성능 기준 충족.
  api 모드는 외부 의존(키·지연·비용)이 있어 p95 기준과 비용 정책 확정 후 확대 권장.

## 3. 향후 과제
1) Rule 지식 확장 + RAG 연동으로 커버리지 확대 (API 의존·비용 절감)
2) Golden Answer 이중 검증으로 Judge 오평가 완충
3) 평가 로그 시계열 적재 → "전일 대비 품질 변화" 자동 리포트 (LLMOps)
