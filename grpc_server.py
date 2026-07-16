"""발표용 로컬 어댑터. 실제 환경에서는 각 Agent를 6001~6006 gRPC 서버로 교체할 수 있습니다."""
AGENT_PORTS={"Interpreter":6001,"Retriever":6002,"Summarizer":6003,"Evaluator":6004,"Critic":6005,"Improver":6006}
def server_status(): return {name:{"port":port,"status":"UP"} for name,port in AGENT_PORTS.items()}
