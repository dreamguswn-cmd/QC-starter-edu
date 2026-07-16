from pathlib import Path
import sys

root = Path(__file__).resolve().parent
required = [
    root / "quality_diagnosis" / "__init__.py",
    root / "quality_diagnosis" / "realtime_evaluator.py",
    root / "app.py",
]
missing = [str(p.relative_to(root)) for p in required if not p.exists()]
if missing:
    print("[FAIL] 누락 파일:")
    for item in missing:
        print(" -", item)
    raise SystemExit(1)

sys.path.insert(0, str(root))
from quality_diagnosis.realtime_evaluator import evaluate_realtime
print("[OK] realtime_evaluator import 성공")
print("[OK] 실행 경로:", root)
