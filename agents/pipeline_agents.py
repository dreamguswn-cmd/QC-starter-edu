from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import csv, re, time

ROOT = Path(__file__).resolve().parents[1]

KEYWORD_MAP = {
    "결제": ["결제", "승인", "카드", "금액"], "주문": ["주문", "내역", "주문안", "주문 안"],
    "쿠폰": ["쿠폰", "할인"], "로그인": ["로그인", "인증번호", "인증"],
    "배송": ["배송", "택배", "도착", "출고"], "환불": ["환불", "취소"],
    "앱": ["앱", "멈", "실행", "이상"], "개인정보": ["개인정보", "삭제", "탈퇴"],
    "재고": ["품절", "재고"], "파손": ["파손", "깨져", "망가"],
    "상담 응대": ["상담원", "불친절", "친절", "응대"],
    "법적 위협": ["신고", "고소", "소송"], "칭찬": ["칭찬", "친절하게", "감사", "만족"]
}

@dataclass
class AgentStep:
    agent: str
    status: str
    output: Any
    latency_ms: int
    evidence: list[str]
    error: str | None = None

class Interpreter:
    port=6001
    def run(self, question: str) -> AgentStep:
        start=time.perf_counter()
        if not question or not question.strip():
            return AgentStep('Interpreter','ERROR',{},0,[], '질문이 비어 있습니다.')
        q=(question.strip().replace('됫','됐').replace('안보','안 보').replace('늦구','늦고')
           .replace('안댐','안 됨').replace('않됌','안 됨').replace('썻는대','썼는데'))
        found=[]
        for intent, words in KEYWORD_MAP.items():
            if any(w in q for w in words): found.append(intent)
        if not found: found=['모호한 문의']
        is_praise = '칭찬' in found and not any(x in q for x in ['불친절','늦','안 됨','오류','불만'])
        out={'normalized_question':q,'intents':found,'keywords':[w for ws in KEYWORD_MAP.values() for w in ws if w in q][:8],
             'category':'칭찬' if is_praise else found[0], 'is_ambiguous':found==['모호한 문의'],
             'is_compound':len([x for x in found if x not in ['법적 위협','칭찬']])>=2,
             'is_praise':is_praise, 'requires_careful_response':'법적 위협' in found}
        return AgentStep('Interpreter','SUCCESS',out,int((time.perf_counter()-start)*1000),found)

class Retriever:
    port=6002
    def __init__(self, csv_path: Path|None=None): self.csv_path=csv_path or ROOT/'voc.csv'
    def run(self, interpreted: dict, fault: str|None=None) -> AgentStep:
        start=time.perf_counter()
        if fault=='retriever_down': return AgentStep('Retriever','ERROR',[],1,[], 'Retriever 서버 연결 실패(포트 6002)')
        if fault=='timeout': time.sleep(0.15); return AgentStep('Retriever','ERROR',[],150,[], 'Retriever 응답 시간 초과')
        path=self.csv_path if fault!='csv_missing' else ROOT/'missing_voc.csv'
        if not path.exists(): return AgentStep('Retriever','ERROR',[],1,[], f'VOC 데이터 파일을 찾을 수 없습니다: {path.name}')
        rows=list(csv.DictReader(path.open(encoding='utf-8-sig')))
        tokens=set(interpreted.get('intents',[])+interpreted.get('keywords',[]))
        scored=[]
        for r in rows:
            hay=' '.join(r.values())
            score=sum(2 if t in (r['category'],r['sub_category']) else 1 for t in tokens if t and t in hay)
            if score: scored.append((score,r))
        scored.sort(key=lambda x:x[0],reverse=True)
        matches=[dict(r, relevance_score=s) for s,r in scored[:5]]
        status='SUCCESS' if matches else 'NO_DATA'
        return AgentStep('Retriever',status,matches,int((time.perf_counter()-start)*1000),[m['voc_id'] for m in matches])

class Summarizer:
    port=6003
    def run(self, question: str, matches: list[dict]) -> AgentStep:
        start=time.perf_counter()
        if not matches:
            out={'summary':'현재 VOC 데이터에서 직접적으로 일치하는 사례를 찾지 못했습니다.','facts':[],
                 'limitations':['추가 로그 또는 주문번호 기반 확인이 필요합니다.']}
            return AgentStep('Summarizer','NO_DATA',out,1,[])
        cats=sorted(set(m['category'] for m in matches)); causes=[m['cause'] for m in matches[:3]]
        out={'summary':f"질문은 {', '.join(cats)} 관련 VOC이며, 주요 가능 원인은 " + '; '.join(causes) + '입니다.',
             'facts':[f"{m['voc_id']}: {m['customer_text']}" for m in matches[:3]],
             'limitations':['VOC 유사 사례 기반 추정이며 실제 거래 로그 확인 전 원인을 확정할 수 없습니다.']}
        return AgentStep('Summarizer','SUCCESS',out,int((time.perf_counter()-start)*1000),[m['voc_id'] for m in matches[:3]])

class Evaluator:
    port=6004
    def run(self, question:str, interpreted:dict, matches:list[dict], summary:dict)->AgentStep:
        start=time.perf_counter(); reasons=[]; score=0
        if interpreted.get('intents') and interpreted['intents']!=['모호한 문의']: score+=30; reasons.append('의도 해석 가능')
        if matches: score+=30; reasons.append('관련 VOC 근거 확보')
        if summary.get('facts'): score+=25; reasons.append('원문 근거 포함')
        if summary.get('limitations'): score+=15; reasons.append('한계 명시')
        out={'relevance_score':score,'is_grounded':bool(matches),'reasons':reasons,'needs_review':score<70}
        return AgentStep('Evaluator','SUCCESS',out,int((time.perf_counter()-start)*1000),reasons)

class Critic:
    port=6005
    def run(self, question:str, matches:list[dict], evaluation:dict)->AgentStep:
        start=time.perf_counter(); risks=[]
        if not matches: risks.append('근거 데이터가 없으므로 특정 원인을 단정하면 안 됩니다.')
        if any(x in question for x in ['결제','환불','개인정보']): risks.append('고위험 업무이므로 본인 확인·거래 로그·정책 확인이 필요합니다.')
        risks += ['VOC 유사도만으로 실제 장애 원인을 확정할 수 없습니다.', '민감정보를 직접 입력받지 않도록 안내해야 합니다.']
        out={'risks':list(dict.fromkeys(risks)),'critical':not matches or any(x in question for x in ['개인정보','중복 결제'])}
        return AgentStep('Critic','SUCCESS',out,int((time.perf_counter()-start)*1000),risks)

class Improver:
    port=6006
    def run(self, question:str, matches:list[dict], summary:dict, critique:dict)->AgentStep:
        start=time.perf_counter()
        if not matches:
            actions=['관련 데이터 없음 안내','추가 로그·주문번호 기반 확인 요청','신규 VOC 유형으로 등록 후 재학습 데이터 검토']
            priority='검토'
        else:
            policies=list(dict.fromkeys(m['policy'] for m in matches[:3]))
            actions=['고객에게 현재 확인 가능한 사실과 미확인 사항을 구분해 안내',*policies,'처리 단계와 예상 소요시간을 추적 가능하게 제공']
            priority='긴급' if any(m['priority']=='긴급' for m in matches) else '높음'
        out={'root_cause_hypothesis':summary.get('summary'),'customer_guidance':actions[0],
             'improvement_actions':actions[1:] if len(actions)>1 else actions,'priority':priority,
             'kpi':['동일 VOC 재발률','평균 처리시간','1차 해결률','고객 재문의율']}
        return AgentStep('Improver','SUCCESS',out,int((time.perf_counter()-start)*1000),actions)
