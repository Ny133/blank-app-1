import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import numpy as np
from folium.plugins import BeautifyIcon

st.set_page_config(layout="wide")
st.title("🏨 서울 호텔 + 주변 관광지 시각화")

api_key = "f0e46463ccf90abd0defd9c79c8568e922e07a835961b1676cdb2065ecc23494"
radius_m = st.slider("관광지 반경 (m)", 500, 2000, 1000, step=100)

# ------------------ 타입 정의 ------------------
TYPE_COLORS = {
    75: "#32CD32", 76: "#1E90FF", 77: "#00CED1", 78: "#9370DB",
    79: "#FFB347", 80: "#A9A9A9", 82: "#FF69B4", 85: "#4682B4"
}

TYPE_NAMES = {75: "레포츠", 76: "관광지", 77: "교통", 78: "문화시설",
              79: "쇼핑", 80: "다른 숙박지", 82: "음식점", 85: "축제/공연/행사"}

TYPE_ICONS = {75: "fire", 76: "flag", 77: "plane", 78: "camera",
              79: "shopping-cart", 80: "home", 82: "cutlery", 85: "music"}

# -------------------------------------------------------
# 🏨 호텔 상세 정보 (주소·연락처 확실하게 가져오기)
# -------------------------------------------------------
def get_hotel_detail(api_key, content_id):
    url = "http://apis.data.go.kr/B551011/EngService2/detailCommon2"
    params = {
        "ServiceKey": api_key,
        "MobileOS": "ETC",
        "MobileApp": "hotel_app",
        "contentId": content_id,
        "contentTypeId": 32,
        "overviewYN": "Y",
        "addrinfoYN": "Y",
        "defaultYN": "Y",
        "_type": "json"
    }
    try:
        res = requests.get(url, params=params)
        data = res.json()
        item = data["response"]["body"]["items"]["item"]

        # 주소 후보 리스트
        address = (
            item.get("addr1") or
            item.get("addr") or
            item.get("address") or
            item.get("addr2") or
            "정보 없음"
        )

        # 연락처 후보 리스트
        phone = (
            item.get("tel") or
            item.get("telname") or
            item.get("phone") or
            "정보 없음"
        )

        return {"address": address, "phone": phone}

    except:
        return {"address": "정보 없음", "phone": "정보 없음"}


# -------------------------------------------------------
# 검색된 호텔 목록 가져오기(searchStay2)
# -------------------------------------------------------
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

    # Dummy price & rating
    df["price"] = np.random.randint(150000, 300000, size=len(df))
    df["rating"] = np.random.uniform(3.0, 5.0, size=len(df)).round(1)

    return df

hotels_df = get_hotels(api_key)
selected_hotel = st.selectbox("호텔 선택", hotels_df["name"])
hotel_info = hotels_df[hotels_df["name"] == selected_hotel].iloc[0]


# -------------------------------------------------------
# 🎯 주변 관광지 목록 가져오기 (locationBasedList2)
# -------------------------------------------------------
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
                "name": t.get("title", ""),
                "lat": float(t.get("mapy", 0)),
                "lng": float(t.get("mapx", 0)),
                "contentid": t.get("contentid"),
                "type": int(t.get("contenttypeid", 0)),
            })
        return results
    except:
        return []

tourist_list = get_tourist_list(api_key, hotel_info["lat"], hotel_info["lng"], radius_m)
tourist_df = pd.DataFrame(tourist_list)
tourist_df["type_name"] = tourist_df["type"].map(TYPE_NAMES)
tourist_df["color"] = tourist_df["type"].map(TYPE_COLORS)


# -------------------------------------------------------
# 관광지 상세 설명 API (detailCommon2)
# -------------------------------------------------------
def get_tourist_detail(api_key, content_id, content_type_id):
    url = "http://apis.data.go.kr/B551011/EngService2/detailCommon2"
    params = {
        "ServiceKey": api_key,
        "MobileOS": "ETC",
        "MobileApp": "hotel_app",
        "contentId": content_id,
        "contentTypeId": content_type_id,
        "overviewYN": "Y",
        "_type": "json"
    }
    try:
        res = requests.get(url, params=params)
        data = res.json()
        item = data["response"]["body"]["items"]["item"]
        return item.get("overview", "상세 설명 없음")
    except:
        return "상세 설명 없음"


# -------------------------------------------------------
# 호텔 이미지(detailImage2)
# -------------------------------------------------------
def get_hotel_images(api_key, content_id):
    url = "http://apis.data.go.kr/B551011/EngService2/detailImage2"
    params = {
        "ServiceKey": api_key,
        "MobileOS": "ETC",
        "MobileApp": "hotel_app",
        "contentId": content_id,
        "imageYN": "Y",
        "_type": "json"
    }
    try:
        res = requests.get(url, params=params)
        data = res.json()
        items = data["response"]["body"]["items"]["item"]

        if isinstance(items, dict):
            return [items.get("originimgurl")]

        return [i.get("originimgurl") for i in items if i.get("originimgurl")]
    except:
        return []


# -------------------------------------------------------
# 🎨 페이지 선택
# -------------------------------------------------------
page = st.radio("페이지 선택", ["호텔 정보", "관광지 보기"], horizontal=True)


# -------------------------------------------------------
# 📌 호텔 정보 페이지
# -------------------------------------------------------
if page == "호텔 정보":
    st.subheader("🏨 선택 호텔 상세 정보")

    detail_info = get_hotel_detail(api_key, hotel_info["contentid"])

    st.markdown(f"""
    **호텔명:** {hotel_info['name']}  
    **주소:** {detail_info['address']}  
    **연락처:** {detail_info['phone']}  
    **평균 가격:** {hotel_info['price']:,}원  
    **평점:** ⭐ {hotel_info['rating']}  
    """)

    # ---------------- 이미지 갤러리 ----------------
    st.markdown("### 📷 호텔 이미지")
    images = get_hotel_images(api_key, hotel_info["contentid"])

    if images:
        st.image(images, width=300)
    else:
        st.write("이미지 없음")

    # ---------------- Top5 관광지 ----------------
    st.markdown("### 🗺 주변 관광지 Top 5 (숙박 제외)")

    tourist_df_filtered = tourist_df[tourist_df["type"] != 80]

    # 거리 계산
    tourist_df_filtered["dist"] = np.sqrt(
        (tourist_df_filtered["lat"] - hotel_info["lat"]) ** 2 +
        (tourist_df_filtered["lng"] - hotel_info["lng"]) ** 2
    )

    top5 = tourist_df_filtered.sort_values("dist").head(5)

    for _, row in top5.iterrows():
        st.write(f"- **{row['name']}** ({row['type_name']})")

    # 예약 링크
    booking_url = f"https://www.booking.com/searchresults.ko.html?ss={hotel_info['name'].replace(' ', '+')}"
    st.markdown(f"[👉 '{hotel_info['name']}' 예약하러 가기]({booking_url})")


# -------------------------------------------------------
# 📌 관광지 보기 페이지
# -------------------------------------------------------
elif page == "관광지 보기":
    st.subheader("📍 호텔 주변 관광지 보기")

    col1, col2 = st.columns([2, 1])

    # ---------------- 지도 ----------------
    with col1:
        m = folium.Map(location=[hotel_info["lat"], hotel_info["lng"]], zoom_start=15)

        folium.Marker(
            location=[hotel_info["lat"], hotel_info["lng"]],
            popup=hotel_info["name"],
            icon=folium.Icon(color="red", icon="hotel", prefix="fa")
        ).add_to(m)

        # 카테고리 선택
        category_list = ["선택 안 함"] + tourist_df["type_name"].dropna().unique().tolist()
        selected_category = st.selectbox("관광지 분류 선택", category_list)
        selected_spot = None

        if selected_category != "선택 안 함":
            group = tourist_df[tourist_df["type_name"] == selected_category]
            spot_list = ["선택 안 함"] + group["name"].tolist()
            selected_name = st.selectbox(f"{selected_category} 선택", spot_list)

            if selected_name != "선택 안 함":
                selected_spot = group[group["name"] == selected_name].iloc[0]

        for _, row in tourist_df.iterrows():
            highlight = selected_spot is not None and row["name"] == selected_spot["name"]
            icon_name = TYPE_ICONS.get(row["type"], "info-sign")

            if highlight:
                icon = BeautifyIcon(
                    icon="star", icon_shape="marker",
                    border_color="yellow", background_color="yellow",
                    text_color="white")
            else:
                icon = BeautifyIcon(
                    icon=icon_name, icon_shape="circle",
                    border_color=row["color"], background_color=row["color"],
                    text_color="white")

            folium.Marker(
                location=[row["lat"], row["lng"]],
                popup=row["name"],
                icon=icon
            ).add_to(m)

        if selected_spot is not None:
            m.location = [selected_spot["lat"], selected_spot["lng"]]
            m.zoom_start = 17

        st_folium(m, width=700, height=550)

    # ---------------- 목록 UI ----------------
    with col2:
        st.markdown("### 관광지 목록")
        if not tourist_df.empty:
            for t_type, group in tourist_df.groupby("type_name"):
                st.markdown(f"#### {t_type}")
                display_df = group[["name", "color"]].copy()
                display_df["색상"] = display_df["color"].apply(
                    lambda x: f'<div style="width:40px; height:15px; background:{x}; border:1px solid #000;"></div>'
                )
                display_df = display_df.drop(columns=["color"])
                st.write(display_df.to_html(index=False, escape=False), unsafe_allow_html=True)
        else:
            st.write("주변 관광지 데이터가 없습니다.")
