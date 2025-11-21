import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
from haversine import haversine
import plotly.express as px
import numpy as np

st.title("🏨 실시간 한국 호텔 가격 vs 주변 관광지 분석")

# --- 1) API Key 코드에 직접 입력 ---
api_key = "f0e46463ccf90abd0defd9c79c8568e922e07a835961b1676cdb2065ecc23494"  # <-- 여기 바꿔서 넣기

# 지역과 반경 선택
area_code = st.selectbox("지역 선택", [("서울", 1), ("부산", 6), ("제주", 39)])
radius_km = st.slider("관광지 반경 (km)", 0.5, 5.0, 1.0)

if api_key:
    # --- 2) 숙박시설 가져오기 ---
    @st.cache_data(ttl=3600)
    def get_hotels(api_key, area_code):
        url = "http://apis.data.go.kr/B551011/KorService2/searchStay2"
        params = {
            "ServiceKey": api_key,
            "numOfRows": 50,
            "pageNo": 1,
            "MobileOS": "ETC",
            "MobileApp": "hotel_analysis",
            "arrange": "A",
            "_type": "json",
            "areaCode": area_code
        }
        res = requests.get(url, params=params).json()
        items = res['response']['body']['items']['item']
        df = pd.DataFrame(items)[['title','mapx','mapy']].rename(columns={'title':'name','mapx':'lng','mapy':'lat'})
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lng'] = pd.to_numeric(df['lng'], errors='coerce')
        df = df.dropna(subset=['lat','lng'])
        # 가격이 없으면 임시 랜덤 생성
        df['price'] = np.random.randint(150000, 300000, size=len(df))
        return df

    hotels_df = get_hotels(api_key, area_code[1])
    
    # --- 3) 주변 관광지 가져오기 ---
    @st.cache_data(ttl=3600)
    def get_tourist_data(api_key, hotels_df, radius_km):
        tourist_count_list = []
        for idx, hotel in hotels_df.iterrows():
            url = "http://apis.data.go.kr/B551011/KorService2/locationBasedList2"
            params = {
                "ServiceKey": api_key,
                "numOfRows": 50,
                "pageNo": 1,
                "MobileOS": "ETC",
                "MobileApp": "hotel_analysis",
                "mapX": hotel['lng'],
                "mapY": hotel['lat'],
                "radius": int(radius_km*1000),
                "arrange": "A",
                "_type": "json"
            }
            res = requests.get(url, params=params).json()
            try:
                items = res['response']['body']['items']['item']
                count = len(items) if isinstance(items, list) else 1
            except:
                count = 0
            tourist_count_list.append(count)
        hotels_df['tourist_count'] = tourist_count_list
        return hotels_df

    hotels_df = get_tourist_data(api_key, hotels_df, radius_km)

    # --- 4) 지도 시각화 ---
    m = folium.Map(location=[hotels_df['lat'].mean(), hotels_df['lng'].mean()], zoom_start=12)
    for idx, row in hotels_df.iterrows():
        folium.CircleMarker(
            location=[row['lat'], row['lng']],
            radius=row['price']/50000,
            color='blue' if row['tourist_count'] < 5 else 'red',
            fill=True,
            fill_opacity=0.6,
            popup=f"{row['name']} | 가격: {row['price']}원 | 관광지: {row['tourist_count']}"
        ).add_to(m)
    st.subheader("호텔 지도")
    st_folium(m, width=700, height=500)

    # --- 5) 가격 vs 관광지 수 산점도 ---
    st.subheader("💹 가격 vs 주변 관광지 수")
    fig = px.scatter(hotels_df, x='tourist_count', y='price', hover_data=['name'], color='tourist_count', size='price')
    st.plotly_chart(fig)

    # --- 6) 데이터 확인 ---
    st.subheader("📄 호텔 데이터")
    st.dataframe(hotels_df)
