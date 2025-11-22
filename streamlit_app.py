import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import numpy as np

st.set_page_config(layout="wide")
st.title("🏨 서울 호텔 + 주변 관광지 시각화")

# 🔑 API Key
api_key = "인증키"

# 관광지 검색 반경
radius_m = st.slider("관광지 반경 (m)", 500, 2000, 1000, step=100)

# -----------------------------------
# 1) 호텔 정보 가져오기
# -----------------------------------
@st.cache_data(ttl=3600)
def get_hotels(api_key):
    url = "http://apis.data.go.kr/B551011/EngService2/searchStay2"
    params = {
        "ServiceKey": api_key,
        "numOfRows": 50,
        "pageNo": 1,
        "MobileOS": "ETC",
        "MobileApp": "hotel_analysis",
        "arrange": "A",
        "_type": "json",
        "areaCode": 1
    }
    res = requests.get(url, params=params, timeout=10)
    data = res.json()
    items = data['response']['body']['items']['item']
    df = pd.DataFrame(items)
    
    df = df[['title','mapx','mapy']].rename(columns={'title':'name','mapx':'lng','mapy':'lat'})
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lng'] = pd.to_numeric(df['lng'], errors='coerce')
    df = df.dropna(subset=['lat','lng'])
    
    # 가짜 가격/평점
    df['price'] = np.random.randint(150000, 300000, size=len(df))
    df['rating'] = np.random.uniform(3.0,5.0, size=len(df)).round(1)
    return df

hotels_df = get_hotels(api_key)

# 호텔 선택
selected_hotel = st.selectbox("호텔 선택", hotels_df['name'])
hotel_info = hotels_df[hotels_df['name']==selected_hotel].iloc[0]

# -----------------------------------
# 2) 주변 관광지 가져오기
# -----------------------------------
@st.cache_data(ttl=3600)
def get_tourist_list(api_key, lat, lng, radius_m):
    url = "http://apis.data.go.kr/B551011/EngService2/locationBasedList2"
    params = {
        "ServiceKey": api_key,
        "numOfRows": 100,
        "pageNo": 1,
        "MobileOS": "ETC",
        "MobileApp": "hotel_analysis",
        "mapX": lng,
        "mapY": lat,
        "radius": radius_m,
        "arrange": "A",
        "_type": "json"
    }
    res = requests.get(url, params=params, timeout=10)
    data = res.json()
    items = data['response']['body']['items']['item']

    if isinstance(items, dict):
        items = [items]

    df = pd.DataFrame(items)
    df['lat'] = pd.to_numeric(df['mapy'], errors='coerce')
    df['lng'] = pd.to_numeric(df['mapx'], errors='coerce')

    type_map = {
        "75":"레포츠", "76":"관광지", "77":"교통",
        "78":"문화시설", "79":"쇼핑", "80":"숙박",
        "82":"음식점", "85":"축제/공연/행사"
    }
    df['type_name'] = df['contenttypeid'].map(type_map)
    df = df[['title','lat','lng','type_name','contenttypeid']]
    df = df.dropna(subset=['lat','lng'])
    return df

tour_df = get_tourist_list(api_key, hotel_info['lat'], hotel_info['lng'], radius_m)

# -----------------------------------
# 3) 관광지 표 + selectbox
# -----------------------------------
st.subheader("📋 주변 관광지 목록 (분류 포함)")
st.dataframe(tour_df[['title','type_name','lat','lng']], use_container_width=True)

tourist_options = ["선택 안 함"] + tour_df['title'].tolist()
selected_spot_name = st.selectbox("강조할 관광지 선택", tourist_options)

if selected_spot_name != "선택 안 함":
    spot_info = tour_df[tour_df['title']==selected_spot_name].iloc[0]
else:
    spot_info = None

# -----------------------------------
# 4) 지도 표시
# -----------------------------------
st.subheader("🗺️ 지도 시각화")
m = folium.Map(location=[hotel_info['lat'], hotel_info['lng']], zoom_start=15)

# 호텔 강조
folium.Marker(
    location=[hotel_info['lat'], hotel_info['lng']],
    popup=f"<b>{hotel_info['name']}</b><br>가격: {hotel_info['price']}<br>별점: {hotel_info['rating']}",
    icon=folium.Icon(color='red', icon='star', prefix='fa')
).add_to(m)

# 관광지 색상 매핑
color_map = {
    "레포츠":"green","관광지":"blue","교통":"gray",
    "문화시설":"purple","쇼핑":"orange",
    "숙박":"darkred","음식점":"pink","축제/공연/행사":"cadetblue"
}

for i, row in tour_df.iterrows():
    highlight = (spot_info is not None) and (row['title']==spot_info['title'])
    folium.CircleMarker(
        location=[row['lat'], row['lng']],
        radius=10 if highlight else 5,
        color="yellow" if highlight else color_map.get(row['type_name'],"blue"),
        fill=True,
        fill_color="yellow" if highlight else color_map.get(row['type_name'],"blue"),
        fill_opacity=0.7 if not highlight else 1,
        popup=f"{row['title']} ({row['type_name']})"
    ).add_to(m)

# 선택된 관광지 중심으로 이동
if spot_info is not None:
    m.location = [spot_info['lat'], spot_info['lng']]
    m.zoom_start = 17

st_folium(m, width=900, height=550, returned_objects=[])

# -----------------------------------
# 5) 호텔 정보
# -----------------------------------
st.subheader("🏨 호텔 정보")
st.write(f"**호텔명:** {hotel_info['name']}")
st.write(f"**가격:** {hotel_info['price']}원")
st.write(f"**별점:** {hotel_info['rating']}")
st.write(f"**주변 관광지 수:** {len(tour_df)}")
