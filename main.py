from utils.pipeline import analyze_voc
from grpc_server import server_status

def analyze_voc_nl_v2(question:str): return analyze_voc(question)
def health_check(): return {"service":"VOC Improve","status":"UP","agents":server_status()}
