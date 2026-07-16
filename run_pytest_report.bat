@echo off
setlocal

if not exist reports mkdir reports

uv run pytest quality_diagnosis\test_pipeline_e2e.py -v -s -rs ^
  --junitxml=reports\junit_result.xml ^
  --html=reports\pytest_report.html ^
  --self-contained-html > reports\pytest_result.txt 2>&1

type reports\pytest_result.txt

echo.
echo ==============================================
echo Streamlit QA와 동일한 품질 판정 보고서 생성 완료
echo ==============================================
echo reports\junit_result.xml
echo reports\pytest_report.html
echo reports\pytest_result.txt
endlocal
