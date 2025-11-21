import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import numpy as np

st.title("🏨 서울 호텔 + 주변 관광지 시각화 (빠른 로딩)")

# ===============================
# 🔑 1) API Key
# ===============================
api_key = "f0e46463ccf90abd0defd9c79c8568e922e07a835961b1676cdb2065ecc23494"

# 관광지 검색 반경
radius_m = st.slider("관광지 반경 (m)", 500, 2000, 1000, step=100)

# ===============================
# 2) 서울 호텔 정보 가져오기
# ===============================
@st.cache_data(ttl=3600)
def get_hotels(api_key):
    url = "http://apis.data.go.kr/B551011/KorService2/searchStay2"
    params = {
        "ServiceKey": api_key,
        "numOfRows": 50,
        "pageNo": 1,
        "MobileOS": "ETC",
        "MobileApp": "hotel_analysis",
        "arrange": "A",
        "_type": "json",
        "areaCode": 1  # 서울
    }
    res = requests.get(url, params=params, timeout=10)
    data = res.json()
    items = data['response']['body']['items']['item']
    df = pd.DataFrame(items)
    for col in ['title','mapx','mapy']:
        if col not in df.columns:
            df[col] = None
    df = df[['title','mapx','mapy']].rename(columns={'title':'name','mapx':'lng','mapy':'lat'})
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lng'] = pd.to_numeric(df['lng'], errors='coerce')
    df = df.dropna(subset=['lat','lng'])
    df['price'] = np.random.randint(150000, 300000, size=len(df))
    df['rating'] = np.random.uniform(3.0,5.0, size=len(df)).round(1)
    return df

hotels_df = get_hotels(api_key)

# ===============================
# 3) 호텔 선택
# ===============================
hotel_names = hotels_df['name'].tolist()
selected_hotel = st.selectbox("호텔 선택", hotel_names)
hotel_info = hotels_df[hotels_df['name']==selected_hotel].iloc[0]

# ===============================
# 4) 선택한 호텔 주변 관광지 수 가져오기
# ===============================
@st.cache_data(ttl=3600)
def get_tourist_count(api_key, lat, lng, radius_m):
    url = "http://apis.data.go.kr/B551011/KorService2/locationBasedList2"
    params = {
        "ServiceKey": api_key,
        "numOfRows": 50,
        "pageNo": 1,
        "MobileOS": "ETC",
        "MobileApp": "hotel_analysis",
        "mapX": lng,
        "mapY": lat,
        "radius": radius_m,
        "arrange": "A",
        "_type": "json"
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        items = data['response']['body']['items']['item']
        if isinstance(items, list):
            return len(items)
        elif isinstance(items, dict):
            return 1
        else:
            return 0
    except:
        return 0

tourist_count = get_tourist_count(api_key, hotel_info['lat'], hotel_info['lng'], radius_m)

# ===============================
# 5) 지도 시각화
# ===============================
m = folium.Map(location=[hotel_info['lat'], hotel_info['lng']], zoom_start=15)

# 호텔 마커
folium.Marker(
    location=[hotel_info['lat'], hotel_info['lng']],
    popup=f"{hotel_info['name']} | 가격: {hotel_info['price']} | 별점: {hotel_info['rating']} | 주변 관광지: {tourist_count}",
    icon=folium.Icon(color='red', icon='hotel', prefix='fa')
).add_to(m)

# 주변 관광지 수만 버블로 표현 (호텔 주변)
folium.CircleMarker(
    location=[hotel_info['lat'], hotel_info['lng']],
    radius=3 + tourist_count/2,
    color='blue',
    fill=True,
    fill_opacity=0.5,
    popup=f"주변 관광지 수: {tourist_count}"
).add_to(m)

# returned_objects=[] 로 설정 → 무한 로딩 방지
st.subheader(f"{selected_hotel} 주변 관광지 지도")
st_folium(m, width=700, height=500, returned_objects=[])

# ===============================
# 6) 호텔 정보 표시
# ===============================
st.subheader("호텔 정보")
st.write(f"**호텔명:** {hotel_info['name']}")
st.write(f"**가격:** {hotel_info['price']}원")
st.write(f"**별점:** {hotel_info['rating']}")
st.write(f"**주변 관광지 수:** {tourist_count}")
