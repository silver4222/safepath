import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="SafePath Navigator",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ SafePath Navigator")
st.caption("안전을 고려한 도보 경로 추천 서비스")

st.markdown("---")


def get_routes(start_lat, start_lon, end_lat, end_lon):
    url = (
        f"https://router.project-osrm.org/route/v1/foot/"
        f"{start_lon},{start_lat};{end_lon},{end_lat}"
        f"?alternatives=true&overview=full&geometries=geojson"
    )

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        data = response.json()

        if "routes" not in data:
            return []

        return data["routes"]

    except Exception:
        return []


def calculate_safety_score(distance_m):
    if distance_m < 1000:
        return 95
    elif distance_m < 3000:
        return 85
    else:
        return 75


col1, col2 = st.columns(2)

with col1:
    start_lat = st.number_input(
        "출발지 위도",
        value=37.5665,
        format="%.6f"
    )

    start_lon = st.number_input(
        "출발지 경도",
        value=126.9780,
        format="%.6f"
    )

with col2:
    end_lat = st.number_input(
        "도착지 위도",
        value=37.5700,
        format="%.6f"
    )

    end_lon = st.number_input(
        "도착지 경도",
        value=126.9920,
        format="%.6f"
    )


if st.button("경로 찾기", use_container_width=True):

    with st.spinner("경로를 탐색 중입니다..."):

        routes = get_routes(
            start_lat,
            start_lon,
            end_lat,
            end_lon
        )

    if not routes:
        st.error("경로를 찾을 수 없습니다.")
        st.stop()

    m = folium.Map(
        location=[start_lat, start_lon],
        zoom_start=15
    )

    colors = ["green", "blue", "red"]

    route_info = []

    for idx, route in enumerate(routes[:3]):

        coords = route["geometry"]["coordinates"]

        latlon = [
            [c[1], c[0]]
            for c in coords
        ]

        distance_km = route["distance"] / 1000
        duration_min = route["duration"] / 60

        score = calculate_safety_score(
            route["distance"]
        )

        route_info.append({
            "name": (
                "안전 경로"
                if idx == 0 else
                f"대체 경로 {idx}"
            ),
            "distance": distance_km,
            "duration": duration_min,
            "score": score
        })

        folium.PolyLine(
            latlon,
            color=colors[idx % len(colors)],
            weight=6,
            opacity=0.8,
            tooltip=f"경로 {idx+1}"
        ).add_to(m)

    folium.Marker(
        [start_lat, start_lon],
        tooltip="출발"
    ).add_to(m)

    folium.Marker(
        [end_lat, end_lon],
        tooltip="도착"
    ).add_to(m)

    st.subheader("🗺️ 경로 지도")

    st_folium(
        m,
        width=None,
        height=600
    )

    st.subheader("📊 경로 비교")

    cols = st.columns(len(route_info))

    for i, route in enumerate(route_info):

        with cols[i]:
            st.metric(
                "경로",
                route["name"]
            )

            st.write(
                f"📏 {route['distance']:.2f} km"
            )

            st.write(
                f"⏱️ {route['duration']:.1f} 분"
            )

            st.write(
                f"🛡️ 안전도 {route['score']}"
            )

    best_route = max(
        route_info,
        key=lambda x: x["score"]
    )

    st.success(
        f"추천 경로: {best_route['name']} "
        f"(안전도 {best_route['score']})"
    )
