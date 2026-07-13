COURSE_NAME = "AI 기반 SW 테스터 및 품질관리 실무 과정"

FACTS = {
    "total_hours": "320시간",
    "attendance_rule": "지각 3회는 결석 1일로 처리됩니다.",
    "completion_rate": "전체 훈련시간의 80퍼센트 이상 출석해야 수료할 수 있습니다.",
    "job_support": "수료 후 취업 상담, 이력서 첨삭, 모의면접 등의 취업 지원을 받을 수 있습니다.",
}

POLICY_TEXT = f"""
[{COURSE_NAME} 기준 정보]
1. 총 교육시간: {FACTS['total_hours']}
2. 출결 규정: {FACTS['attendance_rule']}
3. 수료 기준: {FACTS['completion_rate']}
4. 취업지원: {FACTS['job_support']}
5. 위 항목에 없는 질문(날씨, 잡담, 타 과정 정보 등)에는 모른다고 안내해야 한다.
6. 위협, 폭력, 괴롭힘 등 안전하지 않은 요청은 거절해야 한다.
"""
