# ------------------ 페이지 선택 (상단 탭) ------------------
tab1, tab2 = st.tabs(["호텔 정보", "관광지 보기"])

# ------------------ 호텔 정보 탭 ------------------
with tab1:
    st.subheader("🏨 선택 호텔 정보")
    if not tourist_df.empty:
        type_counts = tourist_df.groupby("type_name").size()
        counts_text = "<br>".join([f"**{name}**: {count}개" for name, count in type_counts.items()])
    else:
        counts_text = "주변 관광지 데이터가 없습니다."
    st.markdown(f"""
    **호텔명:** {hotel_info['name']}  
    **평균 가격:** {hotel_info['price']:,}원  
    **평점:** {hotel_info['rating']}  
    <br>
    **주변 관광지 수:**<br>
    {counts_text}
    """, unsafe_allow_html=True)

# ------------------ 관광지 보기 탭 ------------------
with tab2:
    st.subheader("📍 호텔 주변 관광지 보기")
    
    # 좌우 컬럼
    col1, col2 = st.columns([1, 1])
    
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
        selected_category = st.selectbox("관광지 분류 선택", ["선택 안 함"] + tourist_df["type_name"].unique().tolist())
        selected_spot = None
        if selected_category != "선택 안 함":
            filtered = tourist_df[tourist_df["type_name"] == selected_category]
            selected_name = st.selectbox(f"{selected_category} 내 관광지 선택", ["선택 안 함"] + filtered["name"].tolist())
            if selected_name != "선택 안 함":
                selected_spot = filtered[filtered["name"] == selected_name].iloc[0]
        
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
        
        st_folium(m, width=900, height=550)
    
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
