import pandas as pd


DISTANCES = {
    ("Nashik", "Pune"): 210,
    ("Ahmednagar", "Pune"): 120,
    ("Nashik", "Ahmednagar"): 160,
    ("Ahmednagar", "Ahmednagar"): 20,
    ("Nashik", "Nashik"): 20,
    ("Pune", "Pune"): 20,
}


def get_distance(source, destination):
    if source == destination:
        return 20

    key = (source, destination)

    if key in DISTANCES:
        return DISTANCES[key]

    reverse_key = (destination, source)

    if reverse_key in DISTANCES:
        return DISTANCES[reverse_key]

    return 250


def quality_score(farmer_quality, buyer_quality):
    quality_rank = {
        "A": 3,
        "B": 2,
        "C": 1
    }

    farmer = quality_rank.get(
        str(farmer_quality).upper(),
        1
    )

    buyer = quality_rank.get(
        str(buyer_quality).upper(),
        1
    )

    if farmer >= buyer:
        return 100

    if farmer == buyer - 1:
        return 60

    return 20


def quantity_score(
    farmer_quantity,
    buyer_quantity
):
    if farmer_quantity >= buyer_quantity:
        return 100

    ratio = farmer_quantity / buyer_quantity

    if ratio >= 0.75:
        return 85

    if ratio >= 0.50:
        return 70

    if ratio >= 0.25:
        return 50

    return 20


def price_score(
    farmer_expected_price,
    buyer_max_price
):
    if farmer_expected_price <= buyer_max_price:
        return 100

    difference = (
        farmer_expected_price
        - buyer_max_price
    )

    if difference <= 2:
        return 80

    if difference <= 5:
        return 60

    return 30


def distance_score(distance):
    if distance <= 50:
        return 100

    if distance <= 100:
        return 90

    if distance <= 150:
        return 80

    if distance <= 200:
        return 70

    if distance <= 300:
        return 55

    return 30


def demand_score(
    forecast_demand,
    buyer_quantity
):
    """
    Measures whether forecast demand is sufficient
    to support the buyer's requirement.
    """

    if forecast_demand is None:
        return 50

    if forecast_demand >= buyer_quantity:
        return 100

    ratio = forecast_demand / buyer_quantity

    if ratio >= 0.75:
        return 80

    if ratio >= 0.50:
        return 60

    return 30


def timing_score(
    farmer_date,
    buyer_date
):
    """
    Scores alignment between produce availability
    and buyer requirement date.
    """

    farmer_date = pd.to_datetime(
        farmer_date
    )

    buyer_date = pd.to_datetime(
        buyer_date
    )

    difference = abs(
        (buyer_date - farmer_date).days
    )

    if difference == 0:
        return 100

    if difference == 1:
        return 85

    if difference == 2:
        return 70

    if difference <= 4:
        return 50

    return 30


def calculate_match_score(
    quantity,
    buyer_quantity,
    farmer_quality,
    buyer_quality,
    farmer_price,
    buyer_price,
    distance,
    forecast_demand=None,
    farmer_date=None,
    buyer_date=None
):

    q_score = quantity_score(
        quantity,
        buyer_quantity
    )

    qual_score = quality_score(
        farmer_quality,
        buyer_quality
    )

    p_score = price_score(
        farmer_price,
        buyer_price
    )

    d_score = distance_score(
        distance
    )

    dem_score = demand_score(
        forecast_demand,
        buyer_quantity
    )

    time_score = timing_score(
        farmer_date,
        buyer_date
    )

    # Final weights = 100%
    final_score = (
        q_score * 0.30
        + qual_score * 0.20
        + p_score * 0.20
        + d_score * 0.15
        + dem_score * 0.10
        + time_score * 0.05
    )

    return round(
        final_score,
        1
    )


def find_matches(
    produce,
    buyers,
    forecast_demand=None
):

    results = []

    for _, buyer in buyers.iterrows():

        # Crop compatibility
        if (
            str(buyer["crop"]).lower()
            != str(produce["crop"]).lower()
        ):
            continue

        distance = get_distance(
            produce["district"],
            buyer["district"]
        )

        score = calculate_match_score(
            quantity=float(
                produce["quantity_kg"]
            ),
            buyer_quantity=float(
                buyer["required_quantity_kg"]
            ),
            farmer_quality=produce[
                "quality_grade"
            ],
            buyer_quality=buyer[
                "min_quality"
            ],
            farmer_price=float(
                produce[
                    "expected_price_per_kg"
                ]
            ),
            buyer_price=float(
                buyer[
                    "max_price_per_kg"
                ]
            ),
            distance=distance,
            forecast_demand=forecast_demand,
            farmer_date=produce[
                "available_date"
            ],
            buyer_date=buyer[
                "required_date"
            ]
        )

        results.append({
            "buyer_id": buyer["buyer_id"],
            "buyer_name": buyer["name"],
            "buyer_type": buyer["buyer_type"],
            "location": buyer.get("location", buyer.get("district", "Pune")),
            "district": buyer["district"],
            "required_quantity_kg": buyer["required_quantity_kg"],
            "max_price_per_kg": buyer["max_price_per_kg"],
            "distance_km": distance,
            "match_score": score,
        })

    if not results:
        return pd.DataFrame()

    results_df = pd.DataFrame(
        results
    )

    return results_df.sort_values(
        "match_score",
        ascending=False
    ).reset_index(drop=True)