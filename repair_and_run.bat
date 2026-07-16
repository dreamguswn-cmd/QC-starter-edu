@echo off
cd /d %~dp0
echo [1/3] Phase 6 파일 확인
uv run python check_phase6.py
if errorlevel 1 (
  echo.
  echo 필수 파일이 누락되었습니다. 압축을 새 폴더에 다시 풀어주세요.
  pause
  exit /b 1
)
echo [2/3] 테스트 실행
uv run pytest -v
if errorlevel 1 (
  pause
  exit /b 1
)
echo [3/3] Streamlit 실행
uv run streamlit run app.py
