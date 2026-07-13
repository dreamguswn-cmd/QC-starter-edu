"""Streamlit 품질 리포트 대시보드 — quality/reports/evaluation_result.csv 시각화.

실행: streamlit run dashboard/streamlit_app.py
"""
import subprocess
import urllib.request
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "quality" / "reports" / "evaluation_result.csv"

st.set_page_config(page_title="AI Agent 품질 대시보드", layout="wide")
st.title("🛡️ AI Agent 품질관리 대시보드")


def _is_up(health_url: str, timeout: float = 1.0) -> bool:
    try:
        urllib.request.urlopen(health_url, timeout=timeout)
        return True
    except Exception:
        return False


# ── 모니터링 서비스 실행/열기 ────────────────────────────────
st.subheader("🔌 모니터링 서비스")
mon_cols = st.columns(2)
MONITORING_SERVICES = (
    ("📈 Prometheus", "http://localhost:9090/-/healthy", "http://localhost:9090", "prometheus"),
    ("📊 Grafana", "http://localhost:3000/api/health", "http://localhost:3000", "grafana"),
)
for col, (label, health_url, open_url, compose_service) in zip(mon_cols, MONITORING_SERVICES):
    with col:
        if _is_up(health_url):
            st.success(f"🟢 {label} 실행 중")
            st.link_button(f"{label} 열기", open_url, use_container_width=True)
        else:
            st.error(f"🔴 {label} 꺼져 있음")
            if st.button(f"▶️ {label} 실행", key=f"start_{compose_service}", use_container_width=True):
                with st.spinner(f"{label} 컨테이너 시작 중..."):
                    result = subprocess.run(
                        ["docker", "compose", "up", "-d", compose_service],
                        cwd=BASE_DIR,
                        capture_output=True,
                        text=True,
                    )
                if result.returncode == 0:
                    st.toast(f"{label} 시작 명령 완료 — 상태 새로고침 중")
                else:
                    st.error(f"실행 실패: {result.stderr[-500:]}")
                st.rerun()
st.caption("Docker Desktop이 실행 중이어야 하며, `docker compose`는 portfolio/ 폴더 기준으로 호출됩니다.")
st.divider()

if not CSV_PATH.exists():
    st.error("평가 결과가 없습니다. 먼저 파이프라인을 실행하세요: "
             "`python -m quality.quality_pipeline` 또는 `POST /pipeline/run`")
    st.stop()

df = pd.read_csv(CSV_PATH)
SCORE_COLS = ["accuracy_score", "groundedness_score", "helpfulness_score", "safety_score"]

# ── 모델(mode) 필터 ──────────────────────────────────────────
modes = sorted(df["mode"].unique().tolist())
selected = st.multiselect("모드 필터", modes, default=modes)
view = df[df["mode"].isin(selected)]

# ── 상단 KPI ────────────────────────────────────────────────
total = len(view)
passed = int((view["overall_decision"] == "PASS").sum())
c1, c2, c3, c4 = st.columns(4)
c1.metric("총 평가 건수", total)
c2.metric("PASS", passed)
c3.metric("통과율", f"{passed / total * 100:.1f}%" if total else "-")
c4.metric("평균 점수", f"{view[SCORE_COLS].mean().mean():.2f}" if total else "-")

# ── 종합 의견 ────────────────────────────────────────────────
st.subheader("📋 종합 의견")
if total:
    pass_rate = passed / total * 100
    label_map = {
        "accuracy_score": "정확성",
        "groundedness_score": "근거성",
        "helpfulness_score": "유용성",
        "safety_score": "안전성",
    }
    weakest_col = view[SCORE_COLS].mean().idxmin()
    weakest_label = label_map[weakest_col]
    weakest_score = view[weakest_col].mean()

    cat_pass_rate = (view.assign(p=(view["overall_decision"] == "PASS").astype(int))
                          .groupby("category")["p"].mean() * 100)
    worst_category = cat_pass_rate.idxmin()
    worst_category_rate = cat_pass_rate.min()

    fail_ids = view.loc[view["overall_decision"] != "PASS", "case_id"].tolist()
    verdict = "양호" if pass_rate >= 80 else "주의 필요" if pass_rate >= 60 else "개선 시급"

    st.info(
        f"**종합 판정: {verdict}** — 전체 {total}건 중 {passed}건 통과 (통과율 {pass_rate:.1f}%). "
        f"4개 평가 항목 중 **{weakest_label}**이 평균 {weakest_score:.2f}점으로 가장 낮아 우선 개선이 필요합니다. "
        f"카테고리별로는 **{worst_category}**의 통과율이 {worst_category_rate:.1f}%로 가장 낮습니다."
        + (f" FAIL 케이스: {', '.join(fail_ids)} (하단 상세 참고)" if fail_ids else " FAIL 케이스가 없습니다.")
    )
else:
    st.info("평가 데이터가 없어 종합 의견을 생성할 수 없습니다.")

# ── 케이스별 점수 (빨주노초 배지) ────────────────────────────
st.subheader("케이스별 점수 (색상 표시)")

def badge(v: int) -> str:
    v = int(v)
    if v >= 5:
        return f"🟢 {v}"
    if v >= 4:
        return f"🟡 {v}"
    if v >= 3:
        return f"🟠 {v}"
    return f"🔴 {v}"

styled = view.copy()
for col in SCORE_COLS:
    styled[col] = styled[col].map(badge)
styled["overall_decision"] = styled["overall_decision"].map(
    lambda d: f"✅ {d}" if d == "PASS" else f"❌ {d}"
)
st.dataframe(styled, use_container_width=True, hide_index=True)

# ── 카테고리별 통과율 / 항목별 평균 ──────────────────────────
left, right = st.columns(2)
with left:
    st.subheader("카테고리별 통과율 (%)")
    cat = (view.assign(p=(view["overall_decision"] == "PASS").astype(int))
               .groupby("category")["p"].mean() * 100)
    st.bar_chart(cat)
with right:
    st.subheader("평가 항목별 평균 점수")
    st.bar_chart(view[SCORE_COLS].mean())

# ── FAIL 케이스 상세 ─────────────────────────────────────────
fails = view[view["overall_decision"] != "PASS"]
with st.expander(f"❌ FAIL 케이스 상세 ({len(fails)}건)", expanded=len(fails) > 0):
    if fails.empty:
        st.success("FAIL 케이스가 없습니다.")
    else:
        st.dataframe(fails, use_container_width=True, hide_index=True)
        st.caption("결함은 Jira에 등록해 추적합니다 → docs/defect_report.md 참고")
