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

# ------------------ 호텔 데이터 ------------------
@st.cache_data(ttl=3600)
def get_hotels(api_key):
    url = "http://apis.data.go.kr/B551011/EngService2/searchStay2"
    params = {"ServiceKey": api_key, "numOfRows": 50, "pageNo": 1,
              "MobileOS": "ETC", "MobileApp": "hotel_analysis",
              "arrange": "A", "_type": "json", "areaCode": 1}
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
    params = {"ServiceKey": api_key, "numOfRows": 200, "pageNo":1,
              "MobileOS":"ETC","MobileApp":"hotel_analysis",
              "mapX":lng,"mapY":lat,"radius":radius_m,"arrange":"A","_type":"json"}
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
                "contentid": t.get("contentid")  # 관광지 detail 조회용
            })
        return results
    except:
        return []

tourist_list = get_tourist_list(api_key, hotel_info["lat"], hotel_info["lng"], radius_m)
tourist_df = pd.DataFrame(tourist_list)
tourist_df["type_name"] = tourist_df["type"].map(TYPE_NAMES)
tourist_df["color"] = tourist_df["type"].map(TYPE_COLORS)

# ------------------ 호텔 상세 정보(detailCommon2) ------------------
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
        "_type": "json"
    }
    try:
        res = requests.get(url, params=params)
        data = res.json()
        item = data["response"]["body"]["items"]["item"]
        return {
            "addr1": item.get("addr1", "정보 없음"),
            "addr2": item.get("addr2", ""),
            "tel": item.get("tel", "정보 없음")
        }
    except:
        return {"addr1":"정보 없음", "addr2":"", "tel":"정보 없음"}

# ------------------ 페이지 선택 ------------------
page = st.radio("페이지 선택", ["호텔 정보", "관광지 보기"], horizontal=True)

# ---------- 호텔 정보 페이지 -----------
if page == "호텔 정보":
    st.subheader("🏨 선택 호텔 상세 정보")

    detail_info = get_hotel_detail(api_key, hotel_info["contentid"])
    st.markdown(f"""
    **호텔명:** {hotel_info['name']}  
    **주소:** {detail_info['addr1']} {detail_info['addr2']}  
    **연락처:** {detail_info['tel']}  
    **평균 가격:** {hotel_info['price']:,}원  
    **평점:** ⭐ {hotel_info['rating']}  
    """)

    # 이미지
    st.markdown("### 📷 호텔 이미지")
    def get_hotel_images(api_key, content_id):
        url = "http://apis.data.go.kr/B551011/EngService2/detailImage2"
        params = {"ServiceKey": api_key, "MobileOS": "ETC",
                  "MobileApp": "hotel_app","contentId": content_id,
                  "imageYN":"Y","_type":"json"}
        try:
            res = requests.get(url, params=params)
            data = res.json()
            items = data["response"]["body"]["items"]["item"]
            if isinstance(items, dict):
                return [items.get("originimgurl")]
            return [i.get("originimgurl") for i in items if i.get("originimgurl")]
        except:
            return []
    images = get_hotel_images(api_key, hotel_info["contentid"])
    if images:
        st.image(images, width=300)
    else:
        st.write("이미지 없음")

    # 주변 관광지 Top5
    st.markdown("### 주변 관광지 Top 5")
    tourist_df_filtered = tourist_df[tourist_df["type"] != 80]
    tourist_df_filtered["dist"] = np.sqrt(
        (tourist_df_filtered["lat"] - hotel_info["lat"])**2 +
        (tourist_df_filtered["lng"] - hotel_info["lng"])**2
    )
    top5 = tourist_df_filtered.sort_values("dist").head(5)
    for _, row in top5.iterrows():
        st.write(f"- **{row['name']}** ({row['type_name']})")

    # 리뷰 요약
    st.markdown("### ⭐ 호텔 리뷰 요약")
    dummy_reviews = [
        "Good location and very clean rooms",
        "Bad smell in the hallway",
        "Very friendly staff and good breakfast",
        "Room was a bit dirty but overall fine"
    ]
    st.info(f"""
- 긍정적인 리뷰 수: {sum('good' in r.lower() or 'clean' in r.lower() for r in dummy_reviews)}
- 부정적인 리뷰 수: {sum('bad' in r.lower() or 'dirty' in r.lower() for r in dummy_reviews)}
- 전체 요약: 전반적으로 '{hotel_info['name']}'에 대한 만족도는 양호하며, 청결/위치 관련 언급이 많습니다.
    """)

    booking_url = f"https://www.booking.com/searchresults.ko.html?ss={hotel_info['name'].replace(' ','+')}"
    st.markdown(f"[👉 '{hotel_info['name']}' 예약하러 가기]({booking_url})")

# ---------- 관광지 보기 페이지 -----------
elif page == "관광지 보기":
    st.subheader("📍 호텔 주변 관광지 보기")
    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown("### 지도")
        m = folium.Map(location=[hotel_info["lat"], hotel_info["lng"]], zoom_start=15)
        # 호텔 마커
        folium.Marker(
            location=[hotel_info['lat'], hotel_info['lng']],
            popup=f"{hotel_info['name']} | 가격: {hotel_info['price']} | 별점: {hotel_info['rating']}",
            icon=folium.Icon(color='red', icon='hotel', prefix='fa')
        ).add_to(m)
        # 관광지 마커
        for _, row in tourist_df.iterrows():
            icon_name = TYPE_ICONS.get(row["type"], "info-sign")
            folium.Marker(
                location=[row["lat"], row["lng"]],
                popup=f"{row['name']} ({row['type_name']})",
                icon=BeautifyIcon(icon=icon_name, icon_shape="circle",
                                  border_color=row["color"], text_color="white",
                                  background_color=row["color"], prefix="fa", icon_size=[20,20])
            ).add_to(m)
        st_folium(m, width=700, height=550)
    with col2:
        st.markdown("### 관광지 목록")
        if not tourist_df.empty:
            for t_type, group in tourist_df.groupby("type_name"):
                st.markdown(f"#### {t_type}")
                display_df = group[["name","color"]].rename(columns={"name":"관광지명","color":"색상"})
                display_df["색상"] = display_df["색상"].apply(
                    lambda x: f'<div style="width:40px; height:15px; background:{x}; border:1px solid #000;"></div>'
                )
                st.write(display_df.to_html(index=False, escape=False), unsafe_allow_html=True)
        else:
            st.write("주변 관광지 데이터가 없습니다.")
