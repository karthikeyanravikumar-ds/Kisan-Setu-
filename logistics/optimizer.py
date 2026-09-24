from itertools import permutations


# =========================================================
# DEMO DISTANCE MATRIX
# =========================================================
# Prototype distances in kilometres.
# These are approximate inter-location distances and are
# intended for demonstration of route optimization.
#
# Production version:
# Replace this with live road-network distances from
# Google Maps / OpenStreetMap routing / OSRM / GraphHopper.
# =========================================================

DISTANCES = {

    "Niphad": {
        "Niphad": 0,
        "Lasalgaon": 20,
        "Dindori": 45,
        "Rahata": 95,
        "Sangamner": 110,
        "Kopargaon": 85,
        "Ahmednagar": 135,
        "Nashik": 55,
        "Pune": 210,
    },

    "Lasalgaon": {
        "Niphad": 20,
        "Lasalgaon": 0,
        "Dindori": 35,
        "Rahata": 90,
        "Sangamner": 105,
        "Kopargaon": 80,
        "Ahmednagar": 130,
        "Nashik": 45,
        "Pune": 225,
    },

    "Dindori": {
        "Niphad": 45,
        "Lasalgaon": 35,
        "Dindori": 0,
        "Rahata": 105,
        "Sangamner": 120,
        "Kopargaon": 95,
        "Ahmednagar": 145,
        "Nashik": 25,
        "Pune": 240,
    },

    "Rahata": {
        "Niphad": 95,
        "Lasalgaon": 90,
        "Dindori": 105,
        "Rahata": 0,
        "Sangamner": 35,
        "Kopargaon": 30,
        "Ahmednagar": 85,
        "Nashik": 115,
        "Pune": 185,
    },

    "Sangamner": {
        "Niphad": 110,
        "Lasalgaon": 105,
        "Dindori": 120,
        "Rahata": 35,
        "Sangamner": 0,
        "Kopargaon": 55,
        "Ahmednagar": 70,
        "Nashik": 130,
        "Pune": 165,
    },

    "Kopargaon": {
        "Niphad": 85,
        "Lasalgaon": 80,
        "Dindori": 95,
        "Rahata": 30,
        "Sangamner": 55,
        "Kopargaon": 0,
        "Ahmednagar": 80,
        "Nashik": 105,
        "Pune": 200,
    },

    "Ahmednagar": {
        "Niphad": 135,
        "Lasalgaon": 130,
        "Dindori": 145,
        "Rahata": 85,
        "Sangamner": 70,
        "Kopargaon": 80,
        "Ahmednagar": 0,
        "Nashik": 155,
        "Pune": 120,
    },

    "Nashik": {
        "Niphad": 55,
        "Lasalgaon": 45,
        "Dindori": 25,
        "Rahata": 115,
        "Sangamner": 130,
        "Kopargaon": 105,
        "Ahmednagar": 155,
        "Nashik": 0,
        "Pune": 210,
    },

    "Pune": {
        "Niphad": 210,
        "Lasalgaon": 225,
        "Dindori": 240,
        "Rahata": 185,
        "Sangamner": 165,
        "Kopargaon": 200,
        "Ahmednagar": 120,
        "Nashik": 210,
        "Pune": 0,
    },
}


# =========================================================
# DISTANCE FUNCTION
# =========================================================

def get_distance(origin, destination):

    if origin == destination:
        return 0

    if origin in DISTANCES:
        if destination in DISTANCES[origin]:
            return DISTANCES[origin][destination]

    if destination in DISTANCES:
        if origin in DISTANCES[destination]:
            return DISTANCES[destination][origin]

    # Unknown location
    return 9999


# =========================================================
# ROUTE DISTANCE
# =========================================================

def calculate_route_distance(route):

    total_distance = 0

    for i in range(len(route) - 1):

        origin = route[i]
        destination = route[i + 1]

        distance = get_distance(
            origin,
            destination
        )

        if distance >= 9999:
            return 9999

        total_distance += distance

    return total_distance


# =========================================================
# ROUTE OPTIMIZATION
# =========================================================

def optimize_route(
    locations,
    vehicle_capacity=2500,
    total_load_kg=None
):
    """
    Optimize a small collection + delivery route.

    Parameters
    ----------
    locations : list
        Collection locations followed by destination.

    vehicle_capacity : float
        Maximum vehicle capacity in kg.

    total_load_kg : float, optional
        Total produce load.

    Returns
    -------
    dict
        Optimized route information.
    """

    # Remove duplicates while preserving order
    unique_locations = list(
        dict.fromkeys(
            [str(location) for location in locations]
        )
    )

    if len(unique_locations) < 2:
        raise ValueError(
            "At least one collection point and one "
            "destination are required."
        )

    # -----------------------------------------------------
    # Assume final location is the destination.
    # Collection points are optimized.
    # -----------------------------------------------------

    destination = unique_locations[-1]
    collection_points = unique_locations[:-1]

    # -----------------------------------------------------
    # Capacity validation
    # -----------------------------------------------------

    if total_load_kg is not None:

        total_load_kg = float(total_load_kg)

        if total_load_kg > float(vehicle_capacity):

            raise ValueError(
                f"Load {total_load_kg:.0f} kg exceeds "
                f"vehicle capacity {vehicle_capacity:.0f} kg."
            )

    # -----------------------------------------------------
    # If there is only one collection point
    # -----------------------------------------------------

    if len(collection_points) == 1:

        route = [
            collection_points[0],
            destination
        ]

        distance = calculate_route_distance(route)

    # -----------------------------------------------------
    # For a small number of locations, test all possible
    # collection-point permutations.
    #
    # This is suitable for our prototype.
    # -----------------------------------------------------

    else:

        best_route = None
        best_distance = float("inf")

        for permutation in permutations(
            collection_points
        ):

            route = list(permutation) + [
                destination
            ]

            distance = calculate_route_distance(
                route
            )

            if distance < best_distance:

                best_distance = distance
                best_route = route

        route = best_route
        distance = best_distance

    # -----------------------------------------------------
    # Utilization
    # -----------------------------------------------------

    if vehicle_capacity > 0 and total_load_kg is not None:

        utilization = (
            total_load_kg /
            float(vehicle_capacity)
        ) * 100

    else:

        utilization = None

    return {
        "route": route,
        "total_distance_km": round(
            distance,
            1
        ),
        "total_load_kg": (
            round(total_load_kg, 1)
            if total_load_kg is not None
            else None
        ),
        "vehicle_capacity_kg": float(
            vehicle_capacity
        ),
        "utilization_percent": (
            round(utilization, 1)
            if utilization is not None
            else None
        )
    }