import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import numpy as np

st.set_page_config(layout="wide")
st.title("🏨 서울 호텔 + 주변 관광지 시각화")

api_key = "YOUR_API_KEY"
radius_m = st.slider("관광지 반경 (m)", 500, 2000, 1000, step=100)

# ------------------ 타입 컬러/이름 ------------------
TYPE_COLORS = {75: "green", 76: "blue", 77: "gray", 78: "purple",
               79: "orange", 80: "red", 82: "pink", 85: "cadetblue"}
TYPE_NAMES = {75: "레포츠", 76: "관광지", 77: "교통", 78: "문화시설",
              79: "쇼핑", 80: "숙박", 82: "음식점", 85: "축제/공연/행사"}

# ------------------ 호텔 데이터 ------------------
@st.cache_data(ttl=3600)
def get_hotels(api_key):
    url = "http://apis.data.go.kr/B551011/EngService2/searchStay2"
    params = {
        "ServiceKey": api_key, "numOfRows": 50, "pageNo": 1,
        "MobileOS": "ETC", "MobileApp": "hotel_analysis",
        "arrange": "A", "_type": "json", "areaCode": 1
    }
    res = requests.get(url, params=params)
    data = res.json()
    items = data['response']['body']['items']['item']
    df = pd.DataFrame(items)
    df = df.rename(columns={"title": "name", "mapy": "lat", "mapx": "lng"})
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lng"] = pd.to_numeric(df["lng"], errors="coerce")
    df = df.dropna(subset=["lat","lng"])
    df["price"] = np.random.randint(150000, 300000, size=len(df))
    df["rating"] = np.random.uniform(3.0,5.0, size=len(df)).round(1)
    return df

hotels_df = get_hotels(api_key)
selected_hotel = st.selectbox("호텔 선택", hotels_df["name"])
hotel_info = hotels_df[hotels_df["name"]==selected_hotel].iloc[0]

# ------------------ 관광지 데이터 ------------------
@st.cache_data(ttl=3600)
def get_tourist_list(api_key, lat, lng, radius_m):
    url = "http://apis.data.go.kr/B551011/EngService2/locationBasedList2"
    params = {
        "ServiceKey": api_key, "numOfRows": 200, "pageNo":1,
        "MobileOS":"ETC","MobileApp":"hotel_analysis",
        "mapX":lng,"mapY":lat,"radius":radius_m,"arrange":"A","_type":"json"
    }
    try:
        res = requests.get(url, params=params)
        data = res.json()
        items = data["response"]["body"]["items"]["item"]
        results = []
        for t in items if isinstance(items, list) else [items]:
            results.append({
                "name": t.get("title",""),
                "lat": float(t.get("mapy",0)),
                "lng": float(t.get("mapx",0)),
                "type": int(t.get("contenttypeid",0)),
            })
        return results
    except:
        return []

tourist_list = get_tourist_list(api_key, hotel_info["lat"], hotel_info["lng"], radius_m)
tourist_df = pd.DataFrame(tourist_list)
tourist_df["type_name"] = tourist_df["type"].map(TYPE_NAMES)
tourist_df["color"] = tourist_df["type"].map(TYPE_COLORS)

# ------------------ 분류별 선택 ------------------
st.subheader("📋 관광지 선택 (분류별)")

selected_spot = None
for t_type, group in tourist_df.groupby("type_name"):
    st.markdown(f"### {t_type}")
    spot_options = ["선택 안 함"] + group["name"].tolist()
    choice = st.selectbox(f"{t_type} 선택", spot_options, key=t_type)
    if choice != "선택 안 함":
        selected_spot = group[group["name"]==choice].iloc[0]

# ------------------ 지도 생성 ------------------
st.subheader(f"{selected_hotel} 주변 관광지 지도")
m = folium.Map(location=[hotel_info["lat"], hotel_info["lng"]], zoom_start=15)

# 호텔 강조
folium.Marker(
    location=[hotel_info["lat"], hotel_info["lng"]],
    popup=f"<b>{hotel_info['name']}</b><br>가격: {hotel_info['price']}<br>평점: {hotel_info['rating']}",
    icon=folium.Icon(color="red", icon="star", prefix="fa")
).add_to(m)

# 관광지 표시
for _, row in tourist_df.iterrows():
    highlight = selected_spot is not None and row["name"]==selected_spot["name"]
    folium.CircleMarker(
        location=[row["lat"], row["lng"]],
        radius=10 if highlight else 5,
        color="yellow" if highlight else row["color"],
        fill=True,
        fill_color="yellow" if highlight else row["color"],
        fill_opacity=0.8 if not highlight else 1,
        popup=f"{row['name']} ({row['type_name']})"
    ).add_to(m)

if selected_spot is not None:
    m.location = [selected_spot["lat"], selected_spot["lng"]]
    m.zoom_start = 17

st_folium(m, width=900, height=550)
