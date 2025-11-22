import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import numpy as np

st.set_page_config(layout="wide")
st.title("🏨 서울 호텔 + 주변 관광지 시각화")

api_key = "f0e46463ccf90abd0defd9c79c8568e922e07a835961b1676cdb2065ecc23494"
radius_m = st.slider("관광지 반경 (m)", 500, 2000, 1000, step=100)

# ------------------ 타입 컬러/이름 ------------------
TYPE_COLORS = {
    75: "#32CD32",  # 레포츠 → 라임그린
    76: "#1E90FF",  # 관광지 → 도저블루
    77: "#00CED1",  # 교통 → 다크터쿼이즈
    78: "#9370DB",  # 문화시설 → 미디엄퍼플
    79: "#FFB347",  # 쇼핑 → 연한 주황
    80: "#A9A9A9",  # 다른 숙박지 → 다크그레이
    82: "#FF69B4",  # 음식점 → 핫핑크
    85: "#4682B4"   # 축제/공연/행사 → 스틸블루
}

TYPE_NAMES = {75: "레포츠", 76: "관광지", 77: "교통", 78: "문화시설",
              79: "쇼핑", 80: "다른 숙박지", 82: "음식점", 85: "축제/공연/행사"}

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

# 호텔 정보 표시
st.subheader("🏨 선택 호텔 정보")
st.markdown(f"""
**호텔명:** {hotel_info['name']}  
**가격:** {hotel_info['price']}원  
**평점:** {hotel_info['rating']}  
**위도/경도:** {hotel_info['lat']}, {hotel_info['lng']}
""")

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

# ------------------ 관광지 분류 선택 ------------------
st.subheader("📋 관광지 분류 선택")

# 1) 분류 선택
categories = tourist_df["type_name"].unique().tolist()
selected_category = st.selectbox("관광지 분류 선택", ["선택 안 함"] + categories)

selected_spot = None
# 2) 선택한 분류의 관광지 선택
if selected_category != "선택 안 함":
    filtered = tourist_df[tourist_df["type_name"] == selected_category]
    spot_options = ["선택 안 함"] + filtered["name"].tolist()
    selected_name = st.selectbox(f"{selected_category} 내 관광지 선택", spot_options)
    if selected_name != "선택 안 함":
        selected_spot = filtered[filtered["name"] == selected_name].iloc[0]

# ------------------ 지도 생성 ------------------
m = folium.Map(location=[hotel_info["lat"], hotel_info["lng"]], zoom_start=15)

from folium.plugins import BeautifyIcon

# 호텔 강조 (크기 40x40)
folium.Marker(
    location=[hotel_info['lat'], hotel_info['lng']],
    popup=f"{hotel_info['name']} | 가격: {hotel_info['price']} | 별점: {hotel_info['rating']}",
    icon=folium.Icon(color='red', icon='hotel', prefix='fa')
).add_to(m)



from folium.plugins import BeautifyIcon

from folium.plugins import BeautifyIcon

from folium.plugins import BeautifyIcon

# contentTypeId → 아이콘 매핑
TYPE_ICONS = {
    75: "fire",
    76: "flag",
    77: "plane",
    78: "camera",
    79: "shopping-cart",
    80: "home",
    82: "cutlery",
    85: "music"
}

# 관광지 표시 반복문
from folium.plugins import BeautifyIcon  # 파일 맨 위에서 한 번만

for _, row in tourist_df.iterrows():
    highlight = selected_spot is not None and row["name"] == selected_spot["name"]
    icon_name = TYPE_ICONS.get(row["type"], "info-sign")

    if highlight:
        # 선택 관광지: 노란색 + 크게 강조
        folium.Marker(
            location=[row["lat"], row["lng"]],
            popup=f"{row['name']} ({row['type_name']})",
            icon=BeautifyIcon(
                icon="star",
                icon_shape="marker",
                border_color="yellow",
                text_color="white",
                background_color="yellow",
                prefix="fa",
                icon_size=[30, 30],
                inner_icon_style="margin:0px;"
            )
        ).add_to(m)

    else:
        # 일반 관광지: 타입별 아이콘, 조금 더 작게
        folium.Marker(
            location=[row["lat"], row["lng"]],
            popup=f"{row['name']} ({row['type_name']})",
            icon=BeautifyIcon(
                icon=icon_name,
                icon_shape="circle",
                border_color=row["color"],
                text_color="white",
                background_color=row["color"],
                prefix="fa",
                icon_size=[20, 20],
                inner_icon_style="""
                    font-size:12px;
                    line-height:20px;
                    text-align:center;
                    vertical-align:middle;
                    margin:0px;
                """
            )
        ).add_to(m)



# 선택된 관광지가 있으면 지도 중심 이동
if selected_spot is not None:
    m.location = [selected_spot["lat"], selected_spot["lng"]]
    m.zoom_start = 17

st_folium(m, width=900, height=550)

