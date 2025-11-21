import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import plotly.express as px
import numpy as np

st.title("🏨 한국 호텔 가격 vs 지역 단위 관광지 분석")

# ===============================
# 🔑 1) API Key 코드에 직접 입력
# ===============================
api_key = "f0e46463ccf90abd0defd9c79c8568e922e07a835961b1676cdb2065ecc23494"  # <-- ServiceKey 입력

# 지역 선택
region_options = [("서울", 1), ("부산", 6), ("제주", 39)]
region_name, area_code = st.selectbox("지역 선택", region_options)

if api_key:

    # ===============================
    # 2) 호텔 정보 가져오기
    # ===============================
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
        try:
            res = requests.get(url, params=params, timeout=10)
            data = res.json()
            items = data['response']['body']['items']['item']
            df = pd.DataFrame(items)[['title','mapx','mapy']].rename(
                columns={'title':'name','mapx':'lng','mapy':'lat'}
            )
            df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
            df['lng'] = pd.to_numeric(df['lng'], errors='coerce')
            df = df.dropna(subset=['lat','lng'])
            df['price'] = np.random.randint(150000, 300000, size=len(df))  # 임시 가격
            return df
        except Exception as e:
            st.error(f"호텔 API 오류: {e}")
            st.stop()

    hotels_df = get_hotels(api_key, area_code)

    # ===============================
    # 3) 지역 단위 관광지 수 가져오기
    # ===============================
    @st.cache_data(ttl=3600)
    def get_tourist_count(api_key, area_code):
        url = "http://apis.data.go.kr/B551011/KorService2/areaBasedList2"
        params = {
            "ServiceKey": api_key,
            "numOfRows": 100,
            "pageNo": 1,
            "MobileOS": "ETC",
            "MobileApp": "hotel_analysis",
            "arrange": "A",
            "_type": "json",
            "areaCode": area_code
        }
        try:
            res = requests.get(url, params=params, timeout=10)
            data = res.json()
            items = data['response']['body']['items']['item']
            count = len(items) if isinstance(items, list) else 1
            return count
        except:
            return 0

    tourist_count = get_tourist_count(api_key, area_code)
    hotels_df['tourist_count'] = tourist_count  # 모든 호텔 동일 값

    # ===============================
    # 4) 지도 시각화
    # ===============================
    m = folium.Map(location=[hotels_df['lat'].mean(), hotels_df['lng'].mean()], zoom_start=12)
    for idx, row in hotels_df.iterrows():
        folium.CircleMarker(
            location=[row['lat'], row['lng']],
            radius=row['price']/50000,
            color='blue' if tourist_count < 5 else 'red',
            fill=True,
            fill_opacity=0.6,
            popup=f"{row['name']} | 가격: {row['price']}원 | 관광지: {tourist_count}"
        ).add_to(m)

    st.subheader(f"{region_name} 호텔 지도")
    st_folium(m, width=700, height=500)

    # ===============================
    # 5) 가격 vs 관광지 수 산점도
    # ===============================
    st.subheader("💹 가격 vs 지역 단위 관광지 수")
    fig = px.scatter(hotels_df, x='tourist_count', y='price',
                     hover_data=['name'], color='tourist_count', size='price')
    st.plotly_chart(fig)

    # ===============================
    # 6) 데이터 테이블
    # ===============================
    st.subheader("📄 호텔 데이터")
    st.dataframe(hotels_df)
