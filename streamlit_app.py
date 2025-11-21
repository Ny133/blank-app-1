import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import numpy as np

st.title("🏨 서울 호텔 가격 vs 주변 관광지 분석")

# ===============================
# 🔑 1) API Key 코드에 직접 입력
# ===============================
api_key = "f0e46463ccf90abd0defd9c79c8568e922e07a835961b1676cdb2065ecc23494"  # <-- ServiceKey 입력

# 호텔 반경 관광지 검색 범위
radius_m = st.slider("관광지 반경 (m)", 500, 2000, 1000, step=100)

# ===============================
# 2) 서울 호텔 정보 가져오기
# ===============================
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
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        items = data['response']['body']['items']['item']
        df = pd.DataFrame(items)[['title','mapx','mapy','addr','tel']].rename(
            columns={'title':'name','mapx':'lng','mapy':'lat'}
        )
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lng'] = pd.to_numeric(df['lng'], errors='coerce')
        df = df.dropna(subset=['lat','lng'])
        # 가격과 별점은 API에 없으면 임시 생성
        df['price'] = np.random.randint(150000, 300000, size=len(df))
        df['rating'] = np.random.uniform(3.0,5.0, size=len(df)).round(1)
        return df
    except Exception as e:
        st.error(f"호텔 API 오류: {e}")
        st.stop()

hotels_df = get_hotels(api_key)

# ===============================
# 3) 호텔별 주변 관광지 가져오기
# ===============================
@st.cache_data(ttl=3600)
def get_tourist_info(api_key, hotels_df, radius_m):
    tourist_counts = []
    tourist_lists = []
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
            "radius": radius_m,
            "arrange": "A",
            "_type": "json"
        }
        try:
            res = requests.get(url, params=params, timeout=10)
            data = res.json()
            items = data['response']['body']['items']['item']
            if isinstance(items, list):
                tourist_counts.append(len(items))
                tourist_lists.append([t['title'] for t in items])
            else:
                tourist_counts.append(1)
                tourist_lists.append([items['title']])
        except:
            tourist_counts.append(0)
            tourist_lists.append([])
    hotels_df['tourist_count'] = tourist_counts
    hotels_df['tourist_list'] = tourist_lists
    return hotels_df

hotels_df = get_tourist_info(api_key, hotels_df, radius_m)

# ===============================
# 4) 지도 시각화
# ===============================
m = folium.Map(location=[hotels_df['lat'].mean(), hotels_df['lng'].mean()], zoom_start=12)

for idx, row in hotels_df.iterrows():
    folium.CircleMarker(
        location=[row['lat'], row['lng']],
        radius=5 + row['tourist_count']/2,  # 관광지 수에 비례한 버블 크기
        color='blue',
        fill=True,
        fill_opacity=0.6,
        popup=f"""
        <b>{row['name']}</b><br>
        가격: {row['price']}원<br>
        별점: {row['rating']}<br>
        주변 관광지 수: {row['tourist_count']}<br>
        관광지 목록: {', '.join(row['tourist_list'][:5])} {'...' if len(row['tourist_list'])>5 else ''}
        """
    ).add_to(m)

st.subheader("서울 호텔 지도 (버블 크기 = 주변 관광지 수)")
st_folium(m, width=700, height=500)

# ===============================
# 5) 가격 vs 관광지 수 산점도
# ===============================
st.subheader("💹 가격 vs 주변 관광지 수")
import plotly.express as px
fig = px.scatter(hotels_df, x='tourist_count', y='price',
                 hover_data=['name','rating'], size='tourist_count', color='rating')
st.plotly_chart(fig)

# ===============================
# 6) 데이터 테이블
# ===============================
st.subheader("📄 호텔 데이터")
st.dataframe(hotels_df[['name','price','rating','tourist_count','tourist_list']])
