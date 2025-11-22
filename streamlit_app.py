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
            })
        return results
    except:
        return []

tourist_list = get_tourist_list(api_key, hotel_info["lat"], hotel_info["lng"], radius_m)
tourist_df = pd.DataFrame(tourist_list)
tourist_df["type_name"] = tourist_df["type"].map(TYPE_NAMES)
tourist_df["color"] = tourist_df["type"].map(TYPE_COLORS)

# ------------------ 페이지 선택 (상단 가로 버튼) ------------------
page = st.radio("페이지 선택", ["호텔 정보", "관광지 보기"], horizontal=True)

# ------------------ 호텔 정보 페이지 ------------------
if page == "호텔 정보":
    st.subheader("🏨 선택 호텔 정보")
    if not tourist_df.empty:
        type_counts = tourist_df.groupby("type_name").size()
        counts_text = "<br>".join([f"**{name}**: {count}개" for name, count in type_counts.items()])
    else:
        counts_text = "주변 관광지 데이터가 없습니다."
    st.markdown(f"""
    **호텔명:** {hotel_info['name']}  
    **주소:** {hotel_info.get('address1','')}{(' ' + hotel_info.get('address2','')) if hotel_info.get('address2') else ''}  
    **연락처:** {hotel_info.get('telephone', '정보 없음')}  
    **평균 가격:** {hotel_info['price']:,}원  
    **평점:** {hotel_info['rating']}  
    <br>
    **주변 관광지 수:**<br>
    {counts_text}
    """, unsafe_allow_html=True)

# ------------------ 관광지 보기 페이지 ------------------
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
        
        # 관광지 선택 UI
        category_list = ["선택 안 함"] + tourist_df["type_name"].unique().tolist()
        selected_category = st.selectbox("관광지 분류 선택", category_list)
        selected_spot = None
        
        if selected_category != "선택 안 함":
            filtered = tourist_df[tourist_df["type_name"] == selected_category]
            spot_list = ["선택 안 함"] + filtered["name"].tolist()
            selected_name = st.selectbox(f"{selected_category} 내 관광지 선택", spot_list)
            if selected_name != "선택 안 함":
                selected_spot = filtered[filtered["name"] == selected_name].iloc[0]
        
        # 관광지 마커 표시
        for _, row in tourist_df.iterrows():
            highlight = selected_spot is not None and row["name"] == selected_spot["name"]
            icon_name = TYPE_ICONS.get(row["type"], "info-sign")
            
            if highlight:
                folium.Marker(
                    location=[row["lat"], row["lng"]],
                    popup=f"{row['name']} ({row['type_name']})",
                    icon=BeautifyIcon(
                        icon="star", icon_shape="marker",
                        border_color="yellow", text_color="white", background_color="yellow",
                        prefix="fa", icon_size=[30,30]
                    )
                ).add_to(m)
            else:
                folium.Marker(
                    location=[row["lat"], row["lng"]],
                    popup=f"{row['name']} ({row['type_name']})",
                    icon=BeautifyIcon(
                        icon=icon_name, icon_shape="circle",
                        border_color=row["color"], text_color="white", background_color=row["color"],
                        prefix="fa", icon_size=[20,20]
                    )
                ).add_to(m)
        
        # 선택 관광지 중심 이동
        if selected_spot is not None:
            m.location = [selected_spot["lat"], selected_spot["lng"]]
            m.zoom_start = 17
        
        # 범례
        legend_html = """
        <div style="
            position: fixed;
            top: 80px;
            right: 10px;
            width: 180px;
            background-color: white;
            border:2px solid grey;
            z-index:9999;
            font-size:14px;
            padding: 10px;
            box-shadow: 3px 3px 6px rgba(0,0,0,0.3);
        ">
        <b>[관광지 범례]</b><br>
        """
        for t_type, color in TYPE_COLORS.items():
            icon = TYPE_ICONS.get(t_type, "info-sign")
            name = TYPE_NAMES.get(t_type, "")
            legend_html += f"""<i class="fa fa-{icon}" style="color:{color}; margin-right:5px;"></i> {name} <br>"""
        legend_html += """<i class="fa fa-star" style="color:yellow; margin-right:5px;"></i> 선택 관광지<br>"""
        legend_html += """<i class="fa fa-hotel" style="color:red; margin-right:5px;"></i> 호텔<br></div>"""
        m.get_root().html.add_child(folium.Element(legend_html))
        
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
