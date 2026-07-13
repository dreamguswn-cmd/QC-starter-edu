# pytest 기능 테스트 판정 결과표

- 생성 시각: 2026-07-10 13:27:12
- 총 테스트: 29건 / PASS 29건 / FAIL 0건 / SKIP 0건
- 통과율: 100.0%

| 테스트 수준 | 파일 | 테스트 | 판정 | 소요(ms) |
| --- | --- | --- | --- | --- |
| 테스트 수준 2 — API Test: POST /ask Happy Path 4케이스 응답 스키마·키워드 검증. | test_agent_api.py | test_ask_response_schema | PASS | 8.6 |
| 테스트 수준 2 — API Test: POST /ask Happy Path 4케이스 응답 스키마·키워드 검증. | test_agent_api.py | test_ask_happy_case_education_hours | PASS | 7.9 |
| 테스트 수준 2 — API Test: POST /ask Happy Path 4케이스 응답 스키마·키워드 검증. | test_agent_api.py | test_ask_happy_case_attendance_rule | PASS | 9.9 |
| 테스트 수준 2 — API Test: POST /ask Happy Path 4케이스 응답 스키마·키워드 검증. | test_agent_api.py | test_ask_happy_case_completion_rate | PASS | 5.4 |
| 테스트 수준 2 — API Test: POST /ask Happy Path 4케이스 응답 스키마·키워드 검증. | test_agent_api.py | test_ask_happy_case_job_support | PASS | 5.6 |
| 장애 실습 엔드포인트(/fault-lab) 테스트 — normal · delay · error500 · timeout 시나리오. | test_fault_lab.py | test_normal_response | PASS | 7.1 |
| 장애 실습 엔드포인트(/fault-lab) 테스트 — normal · delay · error500 · timeout 시나리오. | test_fault_lab.py | test_delay_response | PASS | 1005.4 |
| 장애 실습 엔드포인트(/fault-lab) 테스트 — normal · delay · error500 · timeout 시나리오. | test_fault_lab.py | test_error500_response | PASS | 4.6 |
| 장애 실습 엔드포인트(/fault-lab) 테스트 — normal · delay · error500 · timeout 시나리오. | test_fault_lab.py | test_timeout_response | PASS | 1005.3 |
| 테스트 수준 1 — Health Test: 서버 상태 및 Prometheus 메트릭 노출 확인. | test_health.py | test_health_status_ok | PASS | 4.3 |
| 테스트 수준 1 — Health Test: 서버 상태 및 Prometheus 메트릭 노출 확인. | test_health.py | test_health_service_name | PASS | 4.2 |
| 테스트 수준 1 — Health Test: 서버 상태 및 Prometheus 메트릭 노출 확인. | test_health.py | test_metrics_endpoint_exposed | PASS | 5.6 |
| 테스트 수준 4 — Negative Test: 비정상 입력·위험 질문·범위 외 질문 대응 확인. | test_negative_cases.py | test_empty_question_returns_422 | PASS | 6.1 |
| 테스트 수준 4 — Negative Test: 비정상 입력·위험 질문·범위 외 질문 대응 확인. | test_negative_cases.py | test_invalid_mode_returns_422 | PASS | 3.5 |
| 테스트 수준 4 — Negative Test: 비정상 입력·위험 질문·범위 외 질문 대응 확인. | test_negative_cases.py | test_question_too_long_returns_422 | PASS | 5.0 |
| 테스트 수준 4 — Negative Test: 비정상 입력·위험 질문·범위 외 질문 대응 확인. | test_negative_cases.py | test_safety_filter_violence_keyword | PASS | 0.2 |
| 테스트 수준 4 — Negative Test: 비정상 입력·위험 질문·범위 외 질문 대응 확인. | test_negative_cases.py | test_safety_filter_threat_keyword | PASS | 0.2 |
| 테스트 수준 4 — Negative Test: 비정상 입력·위험 질문·범위 외 질문 대응 확인. | test_negative_cases.py | test_safety_filter_harassment_keyword | PASS | 0.2 |
| 테스트 수준 4 — Negative Test: 비정상 입력·위험 질문·범위 외 질문 대응 확인. | test_negative_cases.py | test_out_of_scope_weather | PASS | 0.2 |
| 테스트 수준 4 — Negative Test: 비정상 입력·위험 질문·범위 외 질문 대응 확인. | test_negative_cases.py | test_out_of_scope_instructor_name | PASS | 0.2 |
| 테스트 수준 3 — Quality Pipeline Test: 파이프라인 전체 흐름 + 보고서 3종 생성 확인. | test_quality_pipeline.py | test_rule_validator_pass | PASS | 0.2 |
| 테스트 수준 3 — Quality Pipeline Test: 파이프라인 전체 흐름 + 보고서 3종 생성 확인. | test_quality_pipeline.py | test_rule_validator_fail | PASS | 0.2 |
| 테스트 수준 3 — Quality Pipeline Test: 파이프라인 전체 흐름 + 보고서 3종 생성 확인. | test_quality_pipeline.py | test_test_cases_json_exists | PASS | 0.3 |
| 테스트 수준 3 — Quality Pipeline Test: 파이프라인 전체 흐름 + 보고서 3종 생성 확인. | test_quality_pipeline.py | test_test_cases_structure | PASS | 0.6 |
| 테스트 수준 3 — Quality Pipeline Test: 파이프라인 전체 흐름 + 보고서 3종 생성 확인. | test_quality_pipeline.py | test_pipeline_rule_mode_returns_all_cases | PASS | 5470.6 |
| 테스트 수준 3 — Quality Pipeline Test: 파이프라인 전체 흐름 + 보고서 3종 생성 확인. | test_quality_pipeline.py | test_pipeline_rule_mode_pass_7 | PASS | 2167.7 |
| 테스트 수준 3 — Quality Pipeline Test: 파이프라인 전체 흐름 + 보고서 3종 생성 확인. | test_quality_pipeline.py | test_pipeline_result_has_required_keys | PASS | 2074.6 |
| 테스트 수준 3 — Quality Pipeline Test: 파이프라인 전체 흐름 + 보고서 3종 생성 확인. | test_quality_pipeline.py | test_reports_generated | PASS | 2190.1 |
| 테스트 수준 3 — Quality Pipeline Test: 파이프라인 전체 흐름 + 보고서 3종 생성 확인. | test_quality_pipeline.py | test_evaluation_json_valid | PASS | 2166.7 |
