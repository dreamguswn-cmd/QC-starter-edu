from app.knowledge_base import FACTS, COURSE_NAME, POLICY_TEXT
from app.config import OPENAI_API_KEY, JUDGE_MODEL

REFUSAL_ANSWER = "죄송합니다, 해당 요청은 도와드릴 수 없습니다."
UNKNOWN_ANSWER = "죄송합니다, 해당 내용은 제공된 교육과정 자료에서 확인할 수 없습니다."

API_SYSTEM_PROMPT = (
    "너는 교육과정 안내 챗봇이다. 아래 기준 정보에 근거해서만 답변해야 한다.\n"
    f"{POLICY_TEXT}\n"
    "기준 정보에 없는 내용은 '확인할 수 없습니다'라는 취지로 답하고, "
    "위협·폭력·괴롭힘 등 안전하지 않은 요청은 '도와드릴 수 없습니다'라는 취지로 거절하라."
)

SAFETY_KEYWORDS = ["혼내", "폭력", "협박", "위협", "괴롭히", "때리", "죽이"]
TIME_KEYWORDS = ["교육시간", "총 시간", "몇 시간", "시간인가요"]
ATTENDANCE_KEYWORDS = ["지각", "결석", "출결"]
COMPLETION_KEYWORDS = ["수료", "출석률", "퍼센트", "%"]
JOB_KEYWORDS = ["취업", "이력서", "면접"]


def get_answer(question: str) -> str:
    """규칙 기반 답변: 안전 필터 → 주제 매칭 → 미등록 안내 순."""
    if any(keyword in question for keyword in SAFETY_KEYWORDS):
        return REFUSAL_ANSWER

    answer_parts = []

    if any(keyword in question for keyword in TIME_KEYWORDS):
        answer_parts.append(f"{COURSE_NAME}은 총 {FACTS['total_hours']}으로 구성되어 있습니다.")

    if any(keyword in question for keyword in ATTENDANCE_KEYWORDS):
        answer_parts.append(FACTS["attendance_rule"])

    if any(keyword in question for keyword in COMPLETION_KEYWORDS):
        answer_parts.append(FACTS["completion_rate"])

    if any(keyword in question for keyword in JOB_KEYWORDS):
        answer_parts.append(FACTS["job_support"])

    if not answer_parts:
        return UNKNOWN_ANSWER

    return " ".join(answer_parts)


def get_answer_api(question: str) -> str:
    """OpenAI Responses API 기반 답변. 키 미설정 시 fail-fast."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY가 설정되어 있지 않습니다.")

    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.responses.create(
        model=JUDGE_MODEL,
        input=[
            {"role": "system", "content": API_SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
    )
    return response.output_text
