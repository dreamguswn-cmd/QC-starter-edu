# 독립 LLM Judge QA

기존 `Evaluator`와 `Critic`은 파이프라인 내부 점검입니다. 이 폴더의 QA는 최종 산출물을 별도의 Anthropic 모델로 다시 평가합니다.

## 평가 기준

- 정확성: 25점
- 요약 충실성: 20점
- 개선안 구체성: 20점
- 유용성: 20점
- 안전성: 15점

70점 이상이며 critical failure가 없어야 PASS입니다. 개인정보 노출, 근거 없는 사실 생성, 장애 성공 위장, 결제·환불 확정 오안내는 점수와 무관하게 배포 보류입니다.

## 기본 테스트

API를 호출하지 않고 스키마, 점수 계산, critical failure, CSV 생성을 검증합니다.

```powershell
uv run --project .\VOC_Improve_Phase6_Realtime_Evaluation_v1_8 pytest `
  .\VOC_Improve_Phase6_Realtime_Evaluation_v1_8\quality_diagnosis\test_llm_judge.py -v
```

## 실제 Anthropic 통합 테스트

루트 `.env`에 `ANTHROPIC_API_KEY`를 설정한 뒤 실행합니다. API 비용이 발생합니다.

```powershell
$env:RUN_LLM_JUDGE_TESTS="1"
uv run --project .\VOC_Improve_Phase6_Realtime_Evaluation_v1_8 pytest `
  .\VOC_Improve_Phase6_Realtime_Evaluation_v1_8\quality_diagnosis\test_llm_judge.py -v
```

## 전체 Judge 케이스와 CSV 보고서

```powershell
uv run --project .\VOC_Improve_Phase6_Realtime_Evaluation_v1_8 python -m quality_diagnosis.llm_judge
```

결과는 `quality_diagnosis/reports/llm_judge_result.csv`에 저장됩니다. 빠른 확인에는 `--limit 1`을 사용할 수 있습니다.
