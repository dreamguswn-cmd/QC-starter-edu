import time

from fastapi import HTTPException


def run_fault_scenario(
    scenario: str,
    delay_seconds: float = 3.0
) -> dict:
    """
    장애 실습용 함수

    normal   : 정상 응답
    delay    : 응답 지연
    error500 : 서버 내부 오류
    timeout  : 지연 후 504 타임아웃 오류
    """

    if scenario == "normal":
        return {
            "status": "success",
            "scenario": "normal",
            "message": "정상 응답입니다."
        }

    if scenario == "delay":
        time.sleep(delay_seconds)

        return {
            "status": "success",
            "scenario": "delay",
            "message": f"{delay_seconds}초 동안 응답이 지연되었습니다."
        }

    if scenario == "error500":
        raise HTTPException(
            status_code=500,
            detail="실습용 서버 내부 오류가 발생했습니다."
        )

    if scenario == "timeout":
        time.sleep(delay_seconds)

        raise HTTPException(
            status_code=504,
            detail="실습용 타임아웃 오류가 발생했습니다."
        )

    raise HTTPException(
        status_code=400,
        detail="scenario 값은 normal, delay, error500, timeout 중 하나여야 합니다."
    )
