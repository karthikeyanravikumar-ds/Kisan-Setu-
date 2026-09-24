from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2


# --------------------------------------------------
# ROUTE DISTANCE MATRIX
# Prototype distances in km
# --------------------------------------------------

DISTANCE_MATRIX = {

    "Niphad": {
        "Niphad": 0,
        "Lasalgaon": 45,
        "Dindori": 30,
        "Rahata": 105,
        "Pune": 210,
        "Ahmednagar": 160,
        "Sangamner": 125,
        "Kopargaon": 145,
    },

    "Lasalgaon": {
        "Niphad": 45,
        "Lasalgaon": 0,
        "Dindori": 50,
        "Rahata": 95,
        "Pune": 220,
        "Ahmednagar": 150,
        "Sangamner": 115,
        "Kopargaon": 135,
    },

    "Dindori": {
        "Niphad": 30,
        "Lasalgaon": 50,
        "Dindori": 0,
        "Rahata": 130,
        "Pune": 220,
        "Ahmednagar": 170,
        "Sangamner": 140,
        "Kopargaon": 160,
    },

    "Rahata": {
        "Niphad": 105,
        "Lasalgaon": 95,
        "Dindori": 130,
        "Rahata": 0,
        "Pune": 190,
        "Ahmednagar": 45,
        "Sangamner": 55,
        "Kopargaon": 35,
    },

    "Ahmednagar": {
        "Niphad": 160,
        "Lasalgaon": 150,
        "Dindori": 170,
        "Rahata": 45,
        "Pune": 120,
        "Ahmednagar": 0,
        "Sangamner": 75,
        "Kopargaon": 70,
    },

    "Sangamner": {
        "Niphad": 125,
        "Lasalgaon": 115,
        "Dindori": 140,
        "Rahata": 55,
        "Pune": 160,
        "Ahmednagar": 75,
        "Sangamner": 0,
        "Kopargaon": 75,
    },

    "Kopargaon": {
        "Niphad": 145,
        "Lasalgaon": 135,
        "Dindori": 160,
        "Rahata": 35,
        "Pune": 180,
        "Ahmednagar": 70,
        "Sangamner": 75,
        "Kopargaon": 0,
    },

    "Pune": {
        "Niphad": 210,
        "Lasalgaon": 220,
        "Dindori": 220,
        "Rahata": 190,
        "Pune": 0,
        "Ahmednagar": 120,
        "Sangamner": 160,
        "Kopargaon": 180,
    },
}


# --------------------------------------------------
# GET DISTANCE
# --------------------------------------------------

def get_route_distance(source, destination):

    if source in DISTANCE_MATRIX:
        if destination in DISTANCE_MATRIX[source]:
            return DISTANCE_MATRIX[source][destination]

    return 250


# --------------------------------------------------
# CREATE DISTANCE MATRIX
# --------------------------------------------------

def build_distance_matrix(locations):

    matrix = []

    for source in locations:

        row = []

        for destination in locations:

            distance = get_route_distance(
                source,
                destination
            )

            row.append(distance)

        matrix.append(row)

    return matrix


# --------------------------------------------------
# OPTIMIZE ROUTE
# --------------------------------------------------

def optimize_route(
    locations,
    start_location,
    end_location,
    vehicle_capacity_kg,
    demands_kg
):
    """
    Optimize a collection route using OR-Tools.

    locations:
        List of locations.

    start_location:
        Starting location.

    vehicle_capacity_kg:
        Maximum vehicle capacity.

    demands_kg:
        Produce quantity associated with each location.
    """

    if not locations:
        return None

    # ------------------------------------------
    # Prepare locations
    # ------------------------------------------

    locations = list(locations)

    if start_location not in locations:
        return None

    if end_location not in locations:
        return None

    # ------------------------------------------
    # Distance matrix
    # ------------------------------------------

    distance_matrix = build_distance_matrix(
        locations
    )

    # Convert distance to integer
    distance_matrix = [
        [
            int(distance)
            for distance in row
        ]
        for row in distance_matrix
    ]

    # ------------------------------------------
    # OR-TOOLS MANAGER
    # ------------------------------------------

    start_index = locations.index(start_location)
    end_index = locations.index(end_location)

    manager = pywrapcp.RoutingIndexManager(
    len(locations),
    1,
    [start_index],
    [end_index]
)

    routing = pywrapcp.RoutingModel(
        manager
    )

    # ------------------------------------------
    # DISTANCE CALLBACK
    # ------------------------------------------

    def distance_callback(
        from_index,
        to_index
    ):

        from_node = manager.IndexToNode(
            from_index
        )

        to_node = manager.IndexToNode(
            to_index
        )

        return distance_matrix[
            from_node
        ][
            to_node
        ]

    transit_callback_index = (
        routing.RegisterTransitCallback(
            distance_callback
        )
    )

    routing.SetArcCostEvaluatorOfAllVehicles(
        transit_callback_index
    )

    # ------------------------------------------
    # CAPACITY CALLBACK
    # ------------------------------------------

    def demand_callback(index):

        node = manager.IndexToNode(
            index
        )

        return int(
            demands_kg[node]
        )

    demand_callback_index = (
        routing.RegisterUnaryTransitCallback(
            demand_callback
        )
    )

    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,
        [int(vehicle_capacity_kg)],
        True,
        "Capacity"
    )

    # ------------------------------------------
    # SEARCH PARAMETERS
    # ------------------------------------------

    search_parameters = (
        pywrapcp.DefaultRoutingSearchParameters()
    )

    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy
        .PATH_CHEAPEST_ARC
    )

    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic
        .GUIDED_LOCAL_SEARCH
    )

    search_parameters.time_limit.seconds = 2

    # ------------------------------------------
    # SOLVE
    # ------------------------------------------

    solution = routing.SolveWithParameters(
        search_parameters
    )

    if solution is None:
        return None

    # ------------------------------------------
    # EXTRACT ROUTE
    # ------------------------------------------

    index = routing.Start(0)

    route = []

    total_distance = 0
    total_load = 0

    while not routing.IsEnd(index):

        node = manager.IndexToNode(
            index
        )

        route.append(
            locations[node]
        )

        total_load += demands_kg[node]

        previous_index = index

        index = solution.Value(
            routing.NextVar(index)
        )

        total_distance += routing.GetArcCostForVehicle(
            previous_index,
            index,
            0
        )

    # Add final location
    final_node = manager.IndexToNode(
        index
    )

    route.append(
        locations[final_node]
    )

    return {
        "route": route,
        "total_distance_km": total_distance,
        "total_load_kg": total_load,
        "vehicle_capacity_kg": vehicle_capacity_kg,
        "utilization_percent": round(
            (
                total_load
                / vehicle_capacity_kg
            ) * 100,
            1
        )
    }