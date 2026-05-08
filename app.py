import streamlit as st
from adsorption_model_refactored import (
    adsorbent_data, weights,
    add_adsorbent, calculate_scores,
    apply_environment, rank_adsorbents,
    performance_grade, plot_ranking
)

st.title("활성탄 흡착 성능 예측 및 비교 플랫폼")

# 1. 새 데이터 입력
st.header("새 활성탄 데이터 추가")
name = st.text_input("활성탄 이름")
petroleum = st.number_input("Petroleum", value=0.0)
diesel = st.number_input("Diesel", value=0.0)
mb = st.number_input("MB", value=0.0)
iodine = st.number_input("Iodine", value=0.0)

if st.button("추가하기"):
    add_adsorbent(adsorbent_data, name,
                  petroleum=petroleum,
                  diesel=diesel,
                  mb=mb,
                  iodine=iodine)
    st.success(f"{name} 추가 완료!")

# 2-1. 추가한 데이터 제거
st.header("활성탄 데이터 제거")

remove_name = st.selectbox("제거할 활성탄 선택", list(adsorbent_data.keys()))

if st.button("제거하기"):
    if remove_name in adsorbent_data:
        del adsorbent_data[remove_name]
        st.success(f"{remove_name} 제거 완료!")
    else:
        st.warning("해당 이름은 데이터에 없습니다.")

# 환경 조건 입력
st.header("환경 조건 설정")

# 초기값 설정
if "ph" not in st.session_state:
    st.session_state.ph = 7.0
if "temp" not in st.session_state:
    st.session_state.temp = 25

# 초기화 버튼
if st.button("환경 조건 초기화"):
    st.session_state.ph = 7.0
    st.session_state.temp = 25

# 슬라이더 (동기화된 상태값 사용)
ph = st.slider("pH 값", 1.0, 14.0, st.session_state.ph, key="ph")
temp = st.slider("온도 (°C)", 0, 100, st.session_state.temp, key="temp")


# 3. 계산 및 결과 출력
st.header("결과")
base_results = calculate_scores(adsorbent_data, weights)
final_results = apply_environment(base_results, pH=ph, T=temp)

ranking = rank_adsorbents(final_results)
for rank, (ads, values) in enumerate(ranking, start=1):
    grade = performance_grade(values["conservative"])
    st.write(f"#{rank} {ads} → 점수 {values['conservative']:.2f}, 등급 {grade}")

# 4. 그래프 출력
st.header("랭킹 그래프")
fig = plot_ranking(final_results)   # fig 객체 반환
st.pyplot(fig)                      # Streamlit에 표시
