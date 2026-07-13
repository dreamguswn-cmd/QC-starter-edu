from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """POST /ask 요청. 빈 질문(min_length=1)·잘못된 mode는 422로 자동 거절된다."""

    question: str = Field(..., min_length=1, max_length=500, description="사용자 질문")
    mode: str = Field("rule", pattern="^(rule|api)$", description="rule | api")


class AskResponse(BaseModel):
    question: str
    answer: str
    mode: str
    elapsed_ms: float


class EvaluateResponse(BaseModel):
    question: str
    answer: str
    mode: str
    rule_status: str
    overall_decision: str
    scores: dict
    summary: str
    elapsed_ms: float
