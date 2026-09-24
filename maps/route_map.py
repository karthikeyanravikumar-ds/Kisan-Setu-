import folium
from streamlit_folium import st_folium


# --------------------------------------------------
# PROTOTYPE LOCATION DATABASE
# --------------------------------------------------

LOCATIONS = {
    "Niphad": (20.0833, 73.8000),
    "Lasalgaon": (20.1500, 74.2333),
    "Dindori": (20.0000, 73.8333),
    "Rahata": (19.6500, 74.4833),
    "Sangamner": (19.5700, 74.2100),
    "Kopargaon": (19.8833, 74.4833),

    "Nashik": (19.9975, 73.7898),
    "Ahmednagar": (19.0948, 74.7480),
    "Pune": (18.5204, 73.8567),
}


def get_coordinates(location):

    return LOCATIONS.get(
        str(location),
        LOCATIONS["Nashik"]
    )


# --------------------------------------------------
# OPTIMIZED ROUTE MAP
# --------------------------------------------------

def display_optimized_route_map(
    route,
    farmer_names=None,
    buyer_name=None,
    crop=None,
    total_distance_km=None,
    total_load_kg=None,
    logistics_cost=None
):

    if not route or len(route) < 2:
        return

    farmer_names = farmer_names or {}

    # ------------------------------------------
    # GET ROUTE COORDINATES
    # ------------------------------------------

    route_coordinates = []

    for location in route:

        lat, lon = get_coordinates(location)

        route_coordinates.append(
            [lat, lon]
        )

    # ------------------------------------------
    # CREATE MAP
    # ------------------------------------------

    route_map = folium.Map(
        location=route_coordinates[0],
        zoom_start=7,
        tiles="OpenStreetMap",
        control_scale=True
    )

    # ------------------------------------------
    # ADD MARKERS
    # ------------------------------------------

    for index, location in enumerate(route):

        lat, lon = get_coordinates(location)

        is_destination = (
            index == len(route) - 1
        )

        if is_destination:

            popup_text = (
                f"<b>🛒 Buyer Destination</b><br>"
                f"Location: {location}<br>"
                f"Buyer: {buyer_name or 'Buyer'}"
            )

            if crop:
                popup_text += (
                    f"<br>Crop: {crop}"
                )

            icon_color = "blue"
            icon_name = "shopping-cart"
            tooltip = "🛒 Buyer"

        else:

            farmer_id = farmer_names.get(
                location,
                "Farmer"
            )

            popup_text = (
                f"<b>🌾 Collection Point</b><br>"
                f"Location: {location}<br>"
                f"Farmer: {farmer_id}"
            )

            icon_color = "green"
            icon_name = "leaf"
            tooltip = f"🌾 Stop {index}"

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(
                popup_text,
                max_width=300
            ),
            tooltip=tooltip,
            icon=folium.Icon(
                color=icon_color,
                icon=icon_name
            )
        ).add_to(route_map)

    # ------------------------------------------
    # DRAW OPTIMIZED ROUTE
    # ------------------------------------------

    folium.PolyLine(
        locations=route_coordinates,
        weight=6,
        opacity=0.8,
        tooltip="🚚 OR-Tools Optimized Collection Route"
    ).add_to(route_map)

    # ------------------------------------------
    # FIT MAP TO ROUTE
    # ------------------------------------------

    route_map.fit_bounds(
        route_coordinates
    )

    # ------------------------------------------
    # MAP
    # ------------------------------------------

    st_folium(
        route_map,
        use_container_width=True,
        height=550,
        returned_objects=[]
    )