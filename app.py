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
st.write("지도를 클릭해서 출발지와 도착지를 선택하세요.")

if "start" not in st.session_state:
    st.session_state.start = None

if "end" not in st.session_state:
    st.session_state.end = None


def get_routes(start, end):
    start_lat, start_lon = start
    end_lat, end_lon = end

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

    except:
        return []


def safety_score(distance):
    if distance < 1000:
        return 95
    elif distance < 3000:
        return 85
    else:
        return 75


m = folium.Map(
    location=[36.8151, 127.1139],  # 천안
    zoom_start=14
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
        st.success("출발지가 선택되었습니다.")

    elif st.session_state.end is None:
        st.session_state.end = point
        st.success("도착지가 선택되었습니다.")

st.write("### 선택된 위치")

st.write("출발지:", st.session_state.start)
st.write("도착지:", st.session_state.end)

col1, col2 = st.columns(2)

with col1:
    if st.button("다시 선택"):
        st.session_state.start = None
        st.session_state.end = None
        st.rerun()

with col2:
    if st.button("경로 찾기"):

        if (
            st.session_state.start is None
            or st.session_state.end is None
        ):
            st.warning("출발지와 도착지를 모두 선택하세요.")

        else:
            routes = get_routes(
                st.session_state.start,
                st.session_state.end
            )

            if not routes:
                st.error("경로를 찾을 수 없습니다.")

            else:
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

                for i, route in enumerate(routes[:3]):

                    coords = route["geometry"]["coordinates"]

                    points = [
                        [c[1], c[0]]
                        for c in coords
                    ]

                    distance = route["distance"] / 1000
                    duration = route["duration"] / 60
                    score = safety_score(
                        route["distance"]
                    )

                    infos.append(
                        {
                            "name":
                                "추천 안전 경로"
                                if i == 0
                                else f"대체 경로 {i}",
                            "distance": distance,
                            "duration": duration,
                            "score": score
                        }
                    )

                    folium.PolyLine(
                        points,
                        color=colors[i],
                        weight=6,
                        tooltip=f"경로 {i+1}"
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

                st.subheader("🗺️ 경로")

                st_folium(
                    route_map,
                    height=600,
                    width=None
                )

                st.subheader("📊 경로 비교")

                for info in infos:
                    st.write(
                        f"""
                        **{info['name']}**

                        📏 거리 : {info['distance']:.2f} km

                        ⏱️ 시간 : {info['duration']:.1f} 분

                        🛡️ 안전도 : {info['score']}
                        """
                    )
