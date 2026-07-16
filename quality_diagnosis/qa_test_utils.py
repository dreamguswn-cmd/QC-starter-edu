from __future__ import annotations
from pathlib import Path
import json, csv
from utils.pipeline import analyze_voc
from llm_wrappers.judge import rule_judge,anthropic_judge
ROOT=Path(__file__).resolve().parent

def load_cases(): return json.loads((ROOT/'test_cases.json').read_text(encoding='utf-8'))
def run_case(case,use_llm=False):
    result=analyze_voc(case['question'],case.get('fault'))
    judge=anthropic_judge(case,result) if use_llm else rule_judge(case,result)
    critical=_critical_failure(result)
    if critical: judge['pass']=False; judge['critical_failure']=True; judge['score']=min(judge.get('score',0),69)
    return {'case':case,'result':result,'judge':judge,'critical_failure':critical}
def _critical_failure(result):
    text=json.dumps(result,ensure_ascii=False)
    return any(x in text for x in ['주민등록번호','카드번호 전체']) or ('NO_DATA' in text and '원인입니다' in text and '찾지 못했습니다' not in text)
