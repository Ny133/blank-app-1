import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import numpy as np

st.title("🏨 서울 호텔 + 주변 관광지 시각화")

# 🔑 API Key
api_key = "f0e46463ccf90abd0defd9c79c8568e922e07a835961b1676cdb2065ecc23494"

# 관광지 검색 반경
radius_m = st.slider("관광지 반경 (m)", 500, 2000, 1000, step=100)

# -------------------
# 1) 호텔 정보 가져오기
# -------------------
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

# -------------------
# 2) 호텔 선택
# -------------------
hotel_names = hotels_df['name'].tolist()
selected_hotel = st.selectbox("호텔 선택", hotel_names)
hotel_info = hotels_df[hotels_df['name']==selected_hotel].iloc[0]

# -------------------
# 3) 주변 관광지 정보 가져오기
# -------------------
@st.cache_data(ttl=3600)
def get_tourist_list(api_key, lat, lng, radius_m):
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
        tourist_list = []
        if isinstance(items, list):
            tourist_list = [t.get('title','') for t in items]
        elif isinstance(items, dict):
            tourist_list = [items.get('title','')]
        return tourist_list
    except:
        return []

tourist_list = get_tourist_list(api_key, hotel_info['lat'], hotel_info['lng'], radius_m)

# -------------------
# 4) 지도 시각화
# -------------------
m = folium.Map(location=[hotel_info['lat'], hotel_info['lng']], zoom_start=15)

# 호텔 마커
folium.Marker(
    location=[hotel_info['lat'], hotel_info['lng']],
    popup=f"{hotel_info['name']} | 가격: {hotel_info['price']} | 별점: {hotel_info['rating']}",
    icon=folium.Icon(color='red', icon='hotel', prefix='fa')
).add_to(m)

# 관광지 마커
for t in tourist_list:
    # 좌표는 호텔 중심에서 살짝 랜덤 오프셋
    folium.CircleMarker(
        location=[hotel_info['lat'] + np.random.uniform(-0.001,0.001),
                  hotel_info['lng'] + np.random.uniform(-0.001,0.001)],
        radius=4,
        color='blue',
        fill=True,
        fill_opacity=0.7,
        popup=t
    ).add_to(m)

st.subheader(f"{selected_hotel} 주변 관광지 지도")
st_folium(m, width=700, height=500, returned_objects=[])

# -------------------
# 5) 호텔 정보 + 관광지 목록
# -------------------
st.subheader("호텔 정보 및 주변 관광지")
st.write(f"**호텔명:** {hotel_info['name']}")
st.write(f"**가격:** {hotel_info['price']}원")
st.write(f"**별점:** {hotel_info['rating']}")
st.write(f"**주변 관광지 수:** {len(tourist_list)}")
st.write("**주변 관광지 목록:**")
st.write(tourist_list)
