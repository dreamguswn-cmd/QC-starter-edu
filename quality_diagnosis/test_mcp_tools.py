from main import analyze_voc,analyze_voc_nl_v2,health_check

def test_analyze_voc(): assert analyze_voc('배송이 늦어요')['final']
def test_analyze_voc_nl_v2(): assert analyze_voc_nl_v2('결제가 안 돼요')['final']
def test_health_check():
    h=health_check(); assert h['status']=='UP'; assert len(h['agents'])==6
