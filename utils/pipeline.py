from __future__ import annotations
from dataclasses import asdict
from datetime import datetime
import re
from agents.pipeline_agents import Interpreter,Retriever,Summarizer,Evaluator,Critic,Improver

AGENTS=[Interpreter(),Retriever(),Summarizer(),Evaluator(),Critic(),Improver()]

def analyze_voc(question:str, fault:str|None=None):
    question=_mask_pii(question)
    steps=[]
    i=AGENTS[0].run(question); steps.append(i)
    if i.status=='ERROR': return _finish(question,steps,None)
    r=AGENTS[1].run(i.output,fault); steps.append(r)
    s=AGENTS[2].run(question,r.output if isinstance(r.output,list) else []); steps.append(s)
    e=AGENTS[3].run(question,i.output,r.output if isinstance(r.output,list) else [],s.output); steps.append(e)
    c=AGENTS[4].run(question,r.output if isinstance(r.output,list) else [],e.output); steps.append(c)
    imp=AGENTS[5].run(question,r.output if isinstance(r.output,list) else [],s.output,c.output); steps.append(imp)
    final={'analysis':s.output,'evaluation':e.output,'critique':c.output,'improvement':imp.output,
           'safe_message': s.output['summary'] if r.status!='SUCCESS' else imp.output['customer_guidance']}
    return _finish(question,steps,final)

def _finish(question,steps,final):
    return {'question':question,'timestamp':datetime.now().isoformat(timespec='seconds'),'steps':[asdict(x) for x in steps],
            'final':final,'total_latency_ms':sum(x.latency_ms for x in steps),
            'success':bool(final) and not any(x.status=='ERROR' for x in steps)}

def _mask_pii(text: str) -> str:
    """파이프라인 진입 전에 대표 개인정보를 비가역 표시로 치환한다."""
    if not text:
        return text
    masked = re.sub(r'(?<!\d)(01[016789])[- ]?(\d{3,4})[- ]?(\d{4})(?!\d)', '[전화번호]', text)
    masked = re.sub(r'(?<!\d)(\d{6})[- ]?[1-4]\d{6}(?!\d)', '[주민등록번호]', masked)
    masked = re.sub(r'(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![A-Za-z])', '[이메일]', masked)
    masked = re.sub(r'(?<!\d)(?:\d[ -]?){15,16}(?!\d)', '[카드번호]', masked)
    return masked
