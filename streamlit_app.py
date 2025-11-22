import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import numpy as np

st.title("🏨 서울 호텔 + 주변 관광지 시각화")

api_key = "f0e46463ccf90abd0defd9c79c8568e922e07a835961b1676cdb2065ecc23494"

radius_m = st.slider("관광지 반경 (m)", 500, 2000, 1000, step=100)



# ------------------ 호텔 리스트 ------------------ #
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
    res = requests.get(url, params=params)
    data = res.json()
    items = data['response']['body']['items']['item']
    df = pd.DataFrame(items)

    df = df.rename(columns={"title": "name", "mapy": "lat", "mapx": "lng"})
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lng"] = pd.to_numeric(df["lng"], errors="coerce")
    df = df.dropna(subset=["lat", "lng"])

    df["price"] = np.random.randint(150000, 300000, size=len(df))
    df["rating"] = np.random.uniform(3.0, 5.0, size=len(df)).round(1)
    return df


hotels_df = get_hotels(api_key)

selected_hotel = st.selectbox("호텔 선택", hotels_df["name"])
hotel_info = hotels_df[hotels_df["name"] == selected_hotel].iloc[0]

# ------------------ 관광지 ------------------ #
@st.cache_data(ttl=3600)
def get_tourist_list(api_key, lat, lng, radius_m):
    url = "http://apis.data.go.kr/B551011/EngService2/locationBasedList2"
    params = {
        "ServiceKey": api_key,
        "numOfRows": 200,
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


# ------------------ 지도 생성 ------------------ #
m = folium.Map(location=[hotel_info["lat"], hotel_info["lng"]], zoom_start=15)

# 호텔 마커
folium.Marker(
    location=[hotel_info['lat'], hotel_info['lng']],
    popup=f"{hotel_info['name']} | 가격: {hotel_info['price']} | 별점: {hotel_info['rating']}",
    icon=folium.Icon(color='red', icon='hotel', prefix='fa')
).add_to(m)


# 관광지 색상 매핑
color_map = {
    "레포츠":"green","관광지":"blue","교통":"gray",
    "문화시설":"purple","쇼핑":"orange",
    "음식점":"pink","축제/공연/행사":"cadetblue"
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


# ------------------ 예쁜 표로 목록 출력 ------------------ #
st.subheader("📋 관광지 목록")

st.dataframe(
    tourist_df[["name", "type_name", "lat", "lng"]],
    use_container_width=True
)
