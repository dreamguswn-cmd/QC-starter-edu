# VOC AI Agent Quality Assurance — Final Presentation Edition

## 실행 순서

아래 명령은 VS Code 터미널의 현재 위치가 상위 작업 폴더인 경우를 기준으로 합니다.

```text
VOC_Improve_Phase6_Realtime_Evaluation_v1_12_speed_control\
├─ .env
└─ VOC_Improve_Phase6_Realtime_Evaluation_v1_8\
   ├─ app.py
   ├─ pyproject.toml
   └─ uv.lock
```

### 1. 상위 작업 폴더로 이동

```powershell
cd C:\VOC_Improve_Phase6_Realtime_Evaluation_v1_12_speed_control
```

현재 위치와 파일을 확인합니다.

```powershell
Get-Location
Test-Path .\VOC_Improve_Phase6_Realtime_Evaluation_v1_8\app.py
```

`Test-Path` 결과가 `True`이면 다음 단계로 진행합니다.

### 2. uv 설치 여부 확인

```powershell
uv --version
```

### 3. 프로젝트 의존성 설치 및 동기화

```powershell
uv sync --project .\VOC_Improve_Phase6_Realtime_Evaluation_v1_8
```

### 4. 자동 테스트 실행

```powershell
uv run --project .\VOC_Improve_Phase6_Realtime_Evaluation_v1_8 pytest -q `
  .\VOC_Improve_Phase6_Realtime_Evaluation_v1_8\quality_diagnosis\test_three_axis_validation.py `
  .\VOC_Improve_Phase6_Realtime_Evaluation_v1_8\quality_diagnosis\test_agent_unit.py `
  .\VOC_Improve_Phase6_Realtime_Evaluation_v1_8\quality_diagnosis\test_fault_tolerance.py `
  .\VOC_Improve_Phase6_Realtime_Evaluation_v1_8\quality_diagnosis\test_mcp_tools.py
```

정상 상태에서는 `32 passed`가 출력됩니다.

### 5. Streamlit 앱 실행

```powershell
uv run --project .\VOC_Improve_Phase6_Realtime_Evaluation_v1_8 streamlit run .\VOC_Improve_Phase6_Realtime_Evaluation_v1_8\app.py
```

터미널에 표시되는 `Local URL`을 브라우저에서 엽니다. 일반적으로 다음 주소입니다.

```text
http://localhost:8501
```

### 6. 평가 모드 선택

- API 키 없이 실행: 사이드바에서 `Rule Judge`를 사용합니다.
- Anthropic 독립 평가: `.env`에 `ANTHROPIC_API_KEY`를 설정한 후 `Anthropic 독립 Judge`를 켭니다.
- Judge 모델을 변경하려면 `.env`에 `ANTHROPIC_JUDGE_MODEL`을 설정합니다.

### 7. 앱 종료

Streamlit을 실행한 터미널에서 `Ctrl+C`를 누릅니다.

### 프로젝트 폴더에서 바로 실행하는 단축 명령

터미널의 현재 위치가 `...\VOC_Improve_Phase6_Realtime_Evaluation_v1_8`인 경우:

```powershell
uv sync
uv run streamlit run app.py
```

또는 [run_presentation.bat](run_presentation.bat)을 실행합니다.

## 발표 모드
첫 메뉴 `발표 모드`에서 **전체 발표 데모 시작**을 누르면 다음이 자동 진행됩니다.
1. 대표 VOC 접수
2. 6개 Agent 순차 실행
3. 20개 QA 시나리오 검증
4. 품질·성능·결함 진단
5. 배포 판단 및 보고서 생성

## 단계별 기능
- Phase 1: QA 플랫폼 UI
- Phase 2: Agent 실행 애니메이션
- Phase 3: 실시간 QA 대시보드
- Phase 4: 시각화 및 PDF/Excel/CSV/JSON 보고서
- Phase 5: 원클릭 발표 연출 및 최종 의사결정

## Phase 6: 실시간 질문 평가

사이드바의 **실시간 평가** 메뉴에서 발표자가 즉석 질문을 입력할 수 있습니다.

1. 질문 입력
2. 6개 Agent 순차 실행
3. 검색 근거 기반 품질 평가
4. 정확성·근거성, 완전성, 안전성, 유용성, 일관성 점수 산정
5. PASS/FAIL 및 Critical Failure 판정
6. 개선 권고와 JSON 보고서 다운로드

사전 기대 결과가 없는 질문은 정답 일치율을 계산할 수 없으므로, 이 기능은 제공된 VOC 근거와 답변 구조를 기준으로 품질을 평가합니다.


## v1.5 UI 변경
- 발표 모드의 대표 시연 VOC 선택 목록 제거
- 발표자가 질문을 직접 입력하도록 변경
- 입력 예시 문구와 빈 입력 검증 추가

## 독립 LLM Judge QA

파이프라인 내부 `Evaluator`·`Critic`과 별도로 Anthropic 모델이 최종 산출물을 채점합니다.

```powershell
uv run --project .\VOC_Improve_Phase6_Realtime_Evaluation_v1_8 pytest `
  .\VOC_Improve_Phase6_Realtime_Evaluation_v1_8\quality_diagnosis\test_llm_judge.py -v

uv run --project .\VOC_Improve_Phase6_Realtime_Evaluation_v1_8 python -m quality_diagnosis.llm_judge
```

평가 기준, 실제 API 통합 테스트 방법과 CSV 보고서 설명은
[`quality_diagnosis/README_LLM_JUDGE.md`](quality_diagnosis/README_LLM_JUDGE.md)를 참고합니다.
