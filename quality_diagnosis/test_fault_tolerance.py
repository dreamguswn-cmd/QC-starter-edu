from utils.pipeline import analyze_voc

def test_empty_question():
    out=analyze_voc('')
    assert not out['success']
    assert out['steps'][0]['status']=='ERROR'
def test_retriever_down():
    out=analyze_voc('결제 내역 확인','retriever_down')
    assert any(s['status']=='ERROR' for s in out['steps'])
    assert '찾지 못했습니다' in out['final']['analysis']['summary']
def test_csv_missing():
    out=analyze_voc('배송 상태 확인','csv_missing')
    assert any('파일' in (s.get('error') or '') for s in out['steps'])
def test_empty_result_is_safe():
    out=analyze_voc('홀로그램 상담 연결')
    assert '직접적으로 일치하는 사례를 찾지 못했습니다' in out['final']['analysis']['summary']
