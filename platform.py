import streamlit as st
import numpy as np
import pandas as pd   # ✅ pandas 추가

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

remove_name = st.selectbox(
    "제거할 활성탄 선택",
    list(adsorbent_data.keys())
)

if st.button("제거하기"):
    if remove_name in adsorbent_data:
        del adsorbent_data[remove_name]
        st.success(f"{remove_name} 제거 완료!")
    else:
        st.warning("해당 활성탄이 존재하지 않습니다.")

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

ph = st.slider(
    "pH 값",
    1.0,
    14.0,
    st.session_state.ph,
    step=0.1,   # ✅ 소수점 한 자리 단위로 움직이도록 설정
    key="ph"
)

temp = st.slider("온도 (°C)", 0, 100, st.session_state.temp, key="temp")

st.info(f"""
현재 환경 조건

- pH: {ph}
- Temperature: {temp}°C
""")

# =========================================================
# 4. WEIGHT SETTINGS
# =========================================================

st.header("성능 평가 비중 설정")

chemical_weight = st.slider("화학적 성능 비중", 0.0, 1.0, 0.5, 0.05)
physical_weight = 1.0 - chemical_weight
st.write(f"물리적 성능 비중: {physical_weight:.2f}")

st.subheader("화학적 성능 내부 비율")
petroleum_ratio = st.slider("Petroleum 비율", 0.0, 1.0, 0.7, 0.05)
diesel_ratio = 1.0 - petroleum_ratio
st.write(f"Diesel 비율: {diesel_ratio:.2f}")

st.subheader("물리적 성능 내부 비율")
mb_ratio = st.slider("MB 비율", 0.0, 1.0, 0.6, 0.05)
iodine_ratio = 1.0 - mb_ratio
st.write(f"Iodine 비율: {iodine_ratio:.2f}")

weights = {
    "petroleum": chemical_weight * petroleum_ratio,
    "diesel": chemical_weight * diesel_ratio,
    "mb": physical_weight * mb_ratio,
    "iodine": physical_weight * iodine_ratio
}

st.subheader("최종 적용 가중치")
st.write(weights)
total_weight = sum(weights.values())
st.write(f"총 가중치 합: {total_weight:.2f}")

# =========================================================
# 7. CALCULATION
# =========================================================

base_results = calculate_scores(adsorbent_data, weights)
final_results = apply_environment(base_results, pH=ph, T=temp)
ranking = rank_adsorbents(final_results)

# =========================================================
# 8. RESULTS TABLE
# =========================================================

st.header("흡착제 성능 순위")

table_data = []
for rank, (ads, values) in enumerate(ranking, start=1):
    grade = performance_grade(values["conservative"])
    table_data.append({
        "Rank": rank,
        "Adsorbent": ads,
        "Conservative Score": round(values["conservative"], 2),
        "Potential Score": round(values["potential"], 2),
        "Confidence": round(values["confidence"], 2),
        "Environmental Factor": round(values["env_factor"], 4),
        "Grade": grade
    })

df = pd.DataFrame(table_data)
df = df.set_index("Rank")   # ✅ Rank를 인덱스로 설정해서 기본 인덱스 제거

def highlight_rows(row):
    # Conservative Score가 최대값인 행 강조
    if row["Conservative Score"] == df["Conservative Score"].max():
        return ["background-color: yellow"] * len(row)
    # Grade가 competitive인 행 강조
    elif row["Grade"] == "competitive":
        return ["background-color: yellow"] * len(row)
    else:
        return [""] * len(row)

st.dataframe(
    df.style.apply(highlight_rows, axis=1),
    use_container_width=True
)

csv = df.reset_index().to_csv(index=False).encode("utf-8")  # ✅ Rank 포함해서 CSV 저장
st.download_button(
    label="결과 CSV 다운로드",
    data=csv,
    file_name="adsorbent_ranking.csv",
    mime="text/csv"
)

# =========================================================
# 9. RANKING GRAPH
# =========================================================

st.header("랭킹 그래프")
fig = plot_ranking(final_results)
st.pyplot(fig)
