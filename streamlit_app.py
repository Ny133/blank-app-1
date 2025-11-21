import streamlit as st
from streamlit_pannellum import streamlit_pannellum

# 예시: 관광지별 360 이미지 URL
places = {
    "팔달대교 (대구)": "https://your-domain.com/path/to/paldal_bridge_360.jpg",
    "다른 장소": "https://your-domain.com/path/to/other_place_360.jpg"
}

st.title("VR 관광지 미리보기 서비스")

# 장소 선택
place = st.selectbox("관광지 선택", list(places.keys()))

# 360 파노라마 뷰어 렌더링
panorama_url = places[place]
config = {
    "default": {
        "firstScene": "scene1"
    },
    "scenes": {
        "scene1": {
            "type": "equirectangular",
            "panorama": panorama_url,
            "title": place
        }
    }
}
streamlit_pannellum(config)

# 외부 VR 투어 링크 (예시)
if place == "팔달대교 (대구)":
    st.markdown("[👉 VR 투어 보기 (Look360)](https://look360.kr/your-tour-link)")
