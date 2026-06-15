import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

st.set_page_config(
    page_title="SafePath Navigator",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ SafePath Navigator")
st.caption("안전한 도보 경로 추천 서비스")

# -----------------------
# session_state
# -----------------------
if "start" not in st.session_state:
    st.session_state.start = None

if "end" not in st.session_state:
    st.session_state.end = None

if "routes" not in st.session_state:
    st.session_state.routes = None

# -----------------------
# 장소 검색
# -----------------------
geolocator = Nominatim(
    user_agent="safe_path_app"
)


def search_place(place):
    try:
        location = geolocator.geocode(place)

        if location:
            return (
                location.latitude,
                location.longitude
            )

        return None

    except:
        return None


# -----------------------
# 경로 검색
# -----------------------
def get_routes(start, end):

    start_lat, start_lon = start
    end_lat, end_lon = end

    url = (
        f"https://router.project-osrm.org/route/v1/foot/"
        f"{start_lon},{start_lat};"
        f"{end_lon},{end_lat}"
        f"?alternatives=true"
        f"&overview=full"
        f"&geometries=geojson"
    )

    try:
        response = requests.get(
            url,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        if "routes" not in data:
            return []

        return data["routes"]

    except:
        return []


# -----------------------
# 안전 점수
# -----------------------
def safety_score(distance):

    if distance < 1000:
        return 95
    elif distance < 3000:
        return 85
    else:
        return 75


# -----------------------
# 장소 검색 UI
# -----------------------
st.subheader("🔍 장소 검색")

col1, col2 = st.columns(2)

with col1:
    start_place = st.text_input(
        "출발지 검색",
        placeholder="예: 천안역"
    )

with col2:
    end_place = st.text_input(
        "도착지 검색",
        placeholder="예: 단국대학교 천안캠퍼스"
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

# -----------------------
# 지도
# -----------------------
st.subheader("🗺️ 지도 클릭 선택")

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
    height=500,
    width=None
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

st.write(
    f"📍 출발지 : {st.session_state.start}"
)
st.write(
    f"📍 도착지 : {st.session_state.end}"
)

# -----------------------
# 버튼
# -----------------------
col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 다시 선택"):
        st.session_state.start = None
        st.session_state.end = None
        st.session_state.routes = None
        st.rerun()

with col2:
    if st.button("🚶 경로 찾기"):

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

# -----------------------
# 결과 출력
# -----------------------
if st.session_state.routes:

    st.subheader("🛣️ 추천 경로")

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
        st.session_state.routes[:3]
    ):

        coords = route[
            "geometry"
        ]["coordinates"]

        points = [
            [c[1], c[0]]
            for c in coords
        ]

        distance = (
            route["distance"] / 1000
        )

        duration = (
            route["duration"] / 60
        )

        score = safety_score(
            route["distance"]
        )

        name = (
            "추천 안전 경로"
            if i == 0
            else f"대체 경로 {i}"
        )

        infos.append(
            {
                "name": name,
                "distance": distance,
                "duration": duration,
                "score": score
            }
        )

        folium.PolyLine(
            points,
            color=colors[i],
            weight=6,
            opacity=0.8,
            tooltip=name
        ).add_to(route_map)

    folium.Marker(
        st.session_state.start,
        tooltip="출발지",
        icon=folium.Icon(color="green")
    ).add_to(route_map)

    folium.Marker(
        st.session_state.end,
        tooltip="도착지",
        icon=folium.Icon(color="red")
    ).add_to(route_map)

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
                "경로",
                info["name"]
            )

            st.write(
                f"📏 거리 : {info['distance']:.2f} km"
            )

            st.write(
                f"⏱️ 시간 : {info['duration']:.1f} 분"
            )

            st.write(
                f"🛡️ 안전 점수 : {info['score']}"
            )
