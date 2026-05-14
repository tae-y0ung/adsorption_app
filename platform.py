import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from adsorption_model_refactored import (
    adsorbent_data,
    add_adsorbent,
    calculate_scores,
    apply_environment,
    rank_adsorbents,
    performance_grade,
    plot_ranking
)

# =========================================================
# PANDAS DISPLAY OPTION
# =========================================================
pd.options.display.float_format = "{:.4f}".format

# =========================================================
# PAGE TITLE
# =========================================================
st.title("활성탄 흡착 성능 예측 및 비교 플랫폼")

# =========================================================
# INPUT HELPER
# =========================================================
def convert_input(value):
    value = value.strip()
    if value == "":
        return np.nan
    return float(value)

# =========================================================
# 1. ADD NEW ADSORBENT
# =========================================================
st.header("새 활성탄 데이터 추가")

name = st.text_input("활성탄 이름")
petroleum = st.text_input("Petroleum")
diesel = st.text_input("Diesel")
mb = st.text_input("MB")
iodine = st.text_input("Iodine")

if st.button("추가하기"):
    if name.strip() == "":
        st.warning("활성탄 이름을 입력하세요.")
    elif name in adsorbent_data:
        st.warning("이미 존재하는 활성탄 이름입니다.")
    else:
        try:
            add_adsorbent(
                adsorbent_data,
                name=name,
                petroleum=convert_input(petroleum),
                diesel=convert_input(diesel),
                mb=convert_input(mb),
                iodine=convert_input(iodine)
            )
            st.success(f"{name} 추가 완료!")
        except:
            st.error("숫자를 올바르게 입력하세요.")

# =========================================================
# 2. REMOVE ADSORBENT
# =========================================================
st.header("활성탄 데이터 제거")

remove_name = st.selectbox("제거할 활성탄 선택", list(adsorbent_data.keys()))
if st.button("제거하기"):
    if remove_name in adsorbent_data:
        del adsorbent_data[remove_name]
        st.success(f"{remove_name} 제거 완료!")
    else:
        st.warning("해당 활성탄이 존재하지 않습니다.")

# =========================================================
# 4. WEIGHT SETTINGS
# =========================================================
st.header("성능 평가 비중 설정")

if "chemical_weight" not in st.session_state:
    st.session_state.chemical_weight = 0.5
if "petroleum_ratio" not in st.session_state:
    st.session_state.petroleum_ratio = 0.7
if "mb_ratio" not in st.session_state:
    st.session_state.mb_ratio = 0.6

if st.button("가중치 초기화"):
    st.session_state.chemical_weight = 0.5
    st.session_state.petroleum_ratio = 0.7
    st.session_state.mb_ratio = 0.6

chemical_weight = st.slider("화학적 성능 비중", 0.0, 1.0,
                            st.session_state.chemical_weight, 0.05, key="chemical_weight")
physical_weight = 1.0 - chemical_weight
st.write(f"물리적 성능 비중: {physical_weight:.2f}")

st.subheader("화학적 성능 내부 비율")
petroleum_ratio = st.slider("Petroleum 비율", 0.0, 1.0,
                            st.session_state.petroleum_ratio, 0.05, key="petroleum_ratio")
diesel_ratio = 1.0 - petroleum_ratio
st.write(f"Diesel 비율: {diesel_ratio:.2f}")

st.subheader("물리적 성능 내부 비율")
mb_ratio = st.slider("MB 비율", 0.0, 1.0,
                     st.session_state.mb_ratio, 0.05, key="mb_ratio")
iodine_ratio = 1.0 - mb_ratio
st.write(f"Iodine 비율: {iodine_ratio:.2f}")

weights = {
    "petroleum": chemical_weight * petroleum_ratio,
    "diesel": chemical_weight * diesel_ratio,
    "mb": physical_weight * mb_ratio,
    "iodine": physical_weight * iodine_ratio
}

# =========================================================
# 3. ENVIRONMENT SETTINGS
# =========================================================
st.header("환경 조건 설정")

if "ph" not in st.session_state:
    st.session_state.ph = 7.0
if "temp" not in st.session_state:
    st.session_state.temp = 25

if st.button("환경 조건 초기화"):
    st.session_state.ph = 7.0
    st.session_state.temp = 25

ph = st.slider("pH 값", 1.0, 14.0, st.session_state.ph, step=0.1, key="ph")
temp = st.slider("온도 (°C)", 0, 100, st.session_state.temp, key="temp")

st.info(f"현재 환경 조건\n\n- pH: {ph}\n- Temperature: {temp}°C")

# =========================================================
# 6. CALCULATION
# =========================================================
base_results = calculate_scores(adsorbent_data, weights)
final_results = apply_environment(base_results, pH=ph, T=temp)
ranking = rank_adsorbents(final_results)

# =========================================================
# 7. RESULTS TABLE
# =========================================================
st.header("흡착제 성능 순위")

table_data = []
for rank, (ads, values) in enumerate(ranking, start=1):
    grade = performance_grade(values["conservative"])
    table_data.append({
        "Rank": rank,
        "Adsorbent": ads,
        "Conservative Score": values["conservative"],
        "Potential Score": values["potential"],
        "Confidence": values["confidence"],
        "Environmental Factor": values["env_factor"],
        "Grade": grade
    })

df = pd.DataFrame(table_data)
df = df.round(4)
df = df.set_index("Rank")

def highlight_rows(row):
    if row["Conservative Score"] == df["Conservative Score"].max():
        return ["background-color: yellow"] * len(row)
    elif str(row["Grade"]).lower() == "competitive":
        return ["background-color: yellow"] * len(row)
    else:
        return [""] * len(row)

st.dataframe(
    df.style
      .apply(highlight_rows, axis=1)
      .format({
          "Conservative Score": "{:.4f}",
          "Potential Score": "{:.4f}",
          "Confidence": "{:.4f}",
          "Environmental Factor": "{:.4f}"
      }),
    width="stretch"   # ✅ 최신 Streamlit 방식
)

csv = df.reset_index().to_csv(index=False).encode("utf-8")
st.download_button("결과 CSV 다운로드", data=csv,
                   file_name="adsorbent_ranking.csv", mime="text/csv")

# =========================================================
# 8. RANKING GRAPH
# =========================================================
st.header("랭킹 그래프")
fig = plot_ranking(final_results)
st.pyplot(fig=fig)

# =========================================================
# 9. ENVIRONMENTAL SENSITIVITY ANALYSIS
# =========================================================

st.header("환경 민감도 분석")

selected_adsorbent = st.selectbox(
    "환경 민감도 분석 대상",
    list(final_results.keys())
)

# =========================================================
# pH Range
# =========================================================

ph_range = np.linspace(1, 14, 300)

potential_curve = []
conservative_curve = []

confidence = final_results[selected_adsorbent]["confidence"]

# =========================================================
# Generate Curves
# =========================================================

for ph_value in ph_range:

    # -----------------------------------------------------
    # Base Environmental Factors
    # -----------------------------------------------------

    alpha = 1 / (1 + 10**(6.0 - ph_value))

    surface = 1 - 0.01 * (ph_value - 7)**2

    temperature = 1 - 0.005 * (temp - 25)

    # -----------------------------------------------------
    # Adsorbent-specific Gaussian
    # -----------------------------------------------------

    if selected_adsorbent == "Corn BA700":

        gaussian = (
            np.exp(-((ph_value - 8)**2)/(2*1.0**2))
            * 0.3 + 0.8
        )

    elif selected_adsorbent == "Bagasse ASCB400":

        gaussian = (
            np.exp(-((ph_value - 8.5)**2)/(2*0.8**2))
            * 0.25 + 0.85
        )

    elif selected_adsorbent == "Commercial AC":

        gaussian = (
            np.exp(-((ph_value - 8)**2)/(2*0.7**2))
            * 0.4 + 0.7
        )

    else:

        gaussian = (
            np.exp(-((ph_value - 7)**2)/(2*1.2**2))
            * 0.2 + 0.9
        )

    # -----------------------------------------------------
    # Final Environmental Factor
    # -----------------------------------------------------

    env_factor = (
        alpha
        * surface
        * temperature
        * gaussian
    )

    # -----------------------------------------------------
    # Potential / Conservative
    # -----------------------------------------------------

    base_potential = (
        base_results[selected_adsorbent]["potential"]
    )

    potential_score = (
        base_potential * env_factor
    )

    conservative_score = (
        potential_score * confidence
    )

    potential_curve.append(potential_score)

    conservative_curve.append(conservative_score)

# =========================================================
# Current Position
# =========================================================

current_potential = (
    final_results[selected_adsorbent]["potential"]
)

current_conservative = (
    final_results[selected_adsorbent]["conservative"]
)

# =========================================================
# Plot
# =========================================================

fig2, ax = plt.subplots(figsize=(10, 6))

# ---------------------------------------------------------
# Potential Curve
# ---------------------------------------------------------

ax.plot(
    ph_range,
    potential_curve,
    linewidth=3,
    label="Potential Efficiency"
)

# ---------------------------------------------------------
# Conservative Curve
# ---------------------------------------------------------

ax.plot(
    ph_range,
    conservative_curve,
    linestyle="--",
    linewidth=3,
    label="Conservative Efficiency"
)

# ---------------------------------------------------------
# Current Position Marker
# ---------------------------------------------------------

ax.scatter(
    ph,
    current_conservative,
    s=120,
    zorder=5,
    label=f"Current Condition (pH={ph})"
)

# ---------------------------------------------------------
# pKa Reference
# ---------------------------------------------------------

ax.axvline(
    x=5.4,
    linestyle=":",
    linewidth=2,
    label="Reference pKa ≈ 5.4"
)

# ---------------------------------------------------------
# Labels
# ---------------------------------------------------------

ax.set_title(
    f"{selected_adsorbent} Environmental Sensitivity"
)

ax.set_xlabel("pH")

ax.set_ylabel("Efficiency Score")

ax.grid(True)

ax.legend()

fig2.tight_layout()

# =========================================================
# Show Plot
# =========================================================

st.pyplot(fig2)

# =========================================================
# INTERPRETATION
# =========================================================

st.subheader("환경 조건 해석")

if ph < 5.4:

    st.warning(
        """
현재 조건은 기준 pKa(≈5.4) 이하의 산성 영역입니다.

이 구간에서는 표면 작용기의 이온화가 증가할 수 있으며,
흡착 효율 감소 가능성이 커질 수 있습니다.

현재 마커 위치는 가우시안 곡선의 저효율 영역에
해당합니다.
"""
    )

elif 5.4 <= ph <= 9:

    st.success(
        """
현재 조건은 상대적으로 안정적인 흡착 가능 영역에
위치합니다.

현재 마커는 가우시안 곡선 중심부 근처에 있으며,
환경적 손실이 비교적 적은 상태입니다.
"""
    )

else:

    st.info(
        """
현재 조건은 고 pH 영역입니다.

일부 활성탄에서는 표면 전하 변화로 인해
흡착 효율 변화가 발생할 수 있습니다.
"""
    )

# =========================================================
# CONFIDENCE GAP ANALYSIS
# =========================================================

st.subheader("신뢰도 기반 효율 차이 분석")

gap = (
    current_potential
    - current_conservative
)

st.write(
    f"""
Potential Efficiency와 Conservative Efficiency의 차이:
{gap:.4f}

이 차이는 데이터 부족 및 신뢰도 보정 계수(confidence factor)를
반영한 결과입니다.

즉, 본 플랫폼은 단순 이론 성능뿐 아니라,
현재 확보된 데이터의 신뢰성을 함께 고려하여
보수적 평가를 수행합니다.
"""
) 
