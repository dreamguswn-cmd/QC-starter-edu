from __future__ import annotations
import json, os

def rule_judge(case:dict,result:dict)->dict:
    text=json.dumps(result,ensure_ascii=False)
    req=case.get('required_output',[]); pro=case.get('prohibited_output',[])
    keyword_hits=sum(1 for k in case.get('expected_keywords',[]) if k in text)
    required_hits=sum(1 for k in req if _semantic_required(k,text,result))
    prohibited_hits=sum(1 for k in pro if k in text)
    score=0
    score += 35 if result.get('success') else 0
    score += min(25, keyword_hits*7)
    score += min(30, required_hits*10)
    score += 10 if '단정할 수 없습니다' in text or '확정할 수 없습니다' in text or result.get('final') else 0
    score -= prohibited_hits*20
    score=max(0,min(100,score))
    return {'judge':'Rule Judge','score':score,'pass':score>=70 and prohibited_hits==0,
            'reason':f'키워드 {keyword_hits}개, 필수요소 {required_hits}개, 금지요소 {prohibited_hits}개',
            'keyword_hits':keyword_hits,'required_hits':required_hits,'prohibited_hits':prohibited_hits}

def _semantic_required(term,text,result):
    mapping={'원인 추정':['원인','hypothesis'],'고객 안내':['고객','guidance'],'개선안':['개선','improvement_actions'],
             '우선순위':['우선','priority'],'관련 데이터 없음':['관련 데이터','NO_DATA'],'오류 안내':['ERROR','오류','실패'],
             '개인정보 보호':['민감정보','개인정보'],'복합 문제 분리':['is_compound','intents']}
    return any(x in text for x in mapping.get(term,[term]))

def openai_judge(case,result,model='gpt-4.1-mini'):
    if not os.getenv('OPENAI_API_KEY'): return rule_judge(case,result)|{'warning':'OPENAI_API_KEY가 없어 Rule Judge로 실행'}
    try:
        from openai import OpenAI
        client=OpenAI()
        prompt='당신은 독립적인 소프트웨어 QA LLM Judge입니다. 기대 기준과 실행 결과를 비교하여 JSON만 반환하세요. 필드: score(0~100), pass(boolean), reason, critical_failure(boolean). 근거 없는 추론을 하지 마세요.'
        resp=client.responses.create(model=model,input=[{'role':'system','content':prompt},{'role':'user','content':json.dumps({'case':case,'result':result},ensure_ascii=False)}],temperature=0)
        data=json.loads(resp.output_text)
        return {'judge':'OpenAI LLM Judge',**data}
    except Exception as exc:
        return rule_judge(case,result)|{'warning':f'LLM Judge 실패로 Rule Judge 대체: {exc}'}

def anthropic_judge(case, result, model=None):
    """OpenAI 생성 결과를 독립 모델로 교차 평가한다."""
    if not os.getenv('ANTHROPIC_API_KEY'):
        return rule_judge(case,result)|{'warning':'ANTHROPIC_API_KEY가 없어 Rule Judge로 실행'}
    try:
        from anthropic import Anthropic
        client = Anthropic()
        prompt = (
            '당신은 생성 모델과 독립된 소프트웨어 QA LLM Judge입니다. '
            '기대 기준과 실행 결과를 비교하고 제공된 근거만 사용하세요. '
            'JSON만 반환하세요. 필드: score(0~100), pass(boolean), reason, '
            'critical_failure(boolean). PASS는 70점 이상이며 critical_failure가 없어야 합니다.'
        )
        message = client.messages.create(
            model=model or os.getenv('ANTHROPIC_JUDGE_MODEL', 'claude-sonnet-4-6'),
            max_tokens=700,
            temperature=0,
            system=prompt,
            messages=[{'role':'user','content':json.dumps({'case':case,'result':result},ensure_ascii=False)}],
            output_config={
                'format': {
                    'type': 'json_schema',
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'score': {'type': 'integer'},
                            'pass': {'type': 'boolean'},
                            'reason': {'type': 'string'},
                            'critical_failure': {'type': 'boolean'},
                        },
                        'required': ['score', 'pass', 'reason', 'critical_failure'],
                        'additionalProperties': False,
                    },
                }
            },
        )
        raw = ''.join(block.text for block in message.content if getattr(block, 'type', '') == 'text')
        if not raw.strip():
            raise ValueError(f'Anthropic이 텍스트 응답을 반환하지 않았습니다 (stop_reason={message.stop_reason})')
        data = json.loads(raw)
        return {'judge':'Anthropic Independent LLM Judge',**data}
    except Exception as exc:
        return rule_judge(case,result)|{'warning':f'Anthropic Judge 실패로 Rule Judge 대체: {exc}'}
