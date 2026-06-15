import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

st.set_page_config(
    page_title="안전 귀가 네비게이션",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ 안전 귀가 네비게이션")
st.caption("도보 경로와 예상 시간을 제공합니다.")

# -----------------
# Session State
# -----------------
if "start" not in st.session_state:
    st.session_state.start = None

if "end" not in st.session_state:
    st.session_state.end = None

if "routes" not in st.session_state:
    st.session_state.routes = None

# -----------------
# 장소 검색
# -----------------
geolocator = Nominatim(
    user_agent="safe_path"
)


def search_place(place):
    try:
        loc = geolocator.geocode(place)

        if loc:
            return (
                loc.latitude,
                loc.longitude
            )

        return None

    except:
        return None


# -----------------
# ORS 길찾기
# -----------------
def get_routes(start, end):

    api_key = st.secrets["ORS_API_KEY"]

    url = (
        "https://api.openrouteservice.org/"
        "v2/directions/foot-walking/geojson"
    )

    body = {
        "coordinates": [
            [start[1], start[0]],
            [end[1], end[0]]
        ],
        "alternative_routes": {
            "target_count": 3,
            "share_factor": 0.6
        }
    }

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            url,
            json=body,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        return data["features"]

    except:
        return []


# -----------------
# 장소 검색
# -----------------
st.subheader("🔍 장소 검색")

c1, c2 = st.columns(2)

with c1:
    start_place = st.text_input(
        "출발지",
        placeholder="예) 천안역"
    )

with c2:
    end_place = st.text_input(
        "도착지",
        placeholder="예) 단국대학교 천안캠퍼스"
    )

if st.button("장소 검색"):

    if start_place:
        result = search_place(start_place)

        if result:
            st.session_state.start = result
        else:
            st.error("출발지를 찾을 수 없습니다.")

    if end_place:
        result = search_place(end_place)

        if result:
            st.session_state.end = result
        else:
            st.error("도착지를 찾을 수 없습니다.")

# -----------------
# 지도
# -----------------
st.subheader("🗺️ 지도에서 선택")

m = folium.Map(
    location=[36.8151, 127.1139],
    zoom_start=13
)

if st.session_state.start:
    folium.Marker(
        st.session_state.start,
        tooltip="출발지",
        icon=folium.Icon(color="green")
    ).add_to(m)

if st.session_state.end:
    folium.Marker(
        st.session_state.end,
        tooltip="도착지",
        icon=folium.Icon(color="red")
    ).add_to(m)

map_data = st_folium(
    m,
    height=500
)

clicked = map_data.get("last_clicked")

if clicked:

    point = (
        clicked["lat"],
        clicked["lng"]
    )

    if st.session_state.start is None:
        st.session_state.start = point
        st.rerun()

    elif st.session_state.end is None:
        st.session_state.end = point
        st.rerun()

st.write("출발지 :", st.session_state.start)
st.write("도착지 :", st.session_state.end)

# -----------------
# 버튼
# -----------------
c1, c2 = st.columns(2)

with c1:
    if st.button("다시 선택"):
        st.session_state.start = None
        st.session_state.end = None
        st.session_state.routes = None
        st.rerun()

with c2:
    if st.button("🚶 길찾기"):

        if (
            st.session_state.start is None
            or
            st.session_state.end is None
        ):
            st.warning(
                "출발지와 도착지를 선택하세요."
            )

        else:
            st.session_state.routes = get_routes(
                st.session_state.start,
                st.session_state.end
            )

# -----------------
# 결과 출력
# -----------------
if st.session_state.routes:

    route_map = folium.Map(
        location=st.session_state.start,
        zoom_start=15
    )

    colors = [
        "green",
        "blue",
        "red"
    ]

    infos = []

    for i, route in enumerate(
            st.session_state.routes):

        coords = route["geometry"][
            "coordinates"
        ]

        points = [
            [c[1], c[0]]
            for c in coords
        ]

        summary = route[
            "properties"
        ]["summary"]

        distance = (
            summary["distance"] / 1000
        )

        duration = round(
            summary["duration"] / 60
        )

        name = (
            "추천 경로"
            if i == 0
            else f"대체 경로 {i}"
        )

        infos.append({
            "name": name,
            "distance": distance,
            "duration": duration
        })

        folium.PolyLine(
            points,
            color=colors[i % 3],
            weight=6,
            tooltip=f"{name} · 도보 {duration}분"
        ).add_to(route_map)

    folium.Marker(
        st.session_state.start,
        tooltip="출발"
    ).add_to(route_map)

    folium.Marker(
        st.session_state.end,
        tooltip="도착"
    ).add_to(route_map)

    st.subheader("🗺️ 경로")

    st_folium(
        route_map,
        height=600
    )

    st.subheader("📊 경로 비교")

    cols = st.columns(
        len(infos)
    )

    for i, info in enumerate(infos):

        with cols[i]:

            st.metric(
                info["name"],
                f"{info['duration']}분"
            )

            st.write(
                f"📏 {info['distance']:.2f} km"
            )

            st.write(
                f"🚶 도보 약 {info['duration']}분"
            )
