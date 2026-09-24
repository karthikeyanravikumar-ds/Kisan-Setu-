"""
Pricing, Logistics, and Market Intelligence Engine | Kisan Setu
Computes transportation logistics costs, net farmer realization,
and evaluates buyer offers against Government data.gov.in Mandi benchmarks.
"""

from typing import Dict, Any, Optional, Union
import pandas as pd

from data_ingestion.market_data import get_latest_market_price


def get_mandi_market_benchmark(
    commodity: str,
    district: Optional[str] = None,
    state: str = "Maharashtra",
) -> Dict[str, Any]:
    """
    Retrieve Government of India Mandi market benchmark from data.gov.in API
    with local processed fallback.

    Exposes:
        - modal_price_per_kg: Indicative market benchmark price
        - min_price_per_kg: Mandi session minimum price
        - max_price_per_kg: Mandi session maximum price
        - market: Mandi / APMC yard name
        - arrival_date: Date of market price reporting (YYYY-MM-DD)
        - variety: Produce variety reported by APMC
        - grade: Quality grade reported by APMC
        - is_live: True if obtained from live API call
        - source: Data source provenance
        - disclaimer: Clear guidance on benchmark nature
    """
    bench = get_latest_market_price(commodity=commodity, district=district, state=state)
    bench["disclaimer"] = (
        "Mandi modal price is an indicative regional market benchmark derived from "
        "APMC market arrivals and does not represent a guaranteed farmer purchase price."
    )
    return bench


def calculate_logistics_cost(
    distance_km: float,
    quantity_kg: float,
    logistics_df: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Estimate transportation cost for a produce shipment.
    Selects the most suitable vehicle based on quantity capacity.
    """
    suitable = logistics_df[
        logistics_df["capacity_kg"] >= quantity_kg
    ].sort_values("capacity_kg")

    if suitable.empty:
        suitable = logistics_df.sort_values(
            "capacity_kg",
            ascending=False
        )

    provider = suitable.iloc[0]

    transport_cost = (
        float(provider["base_cost"])
        + (
            float(distance_km)
            * float(provider["cost_per_km"])
        )
    )

    return {
        "provider_name": provider["provider_name"],
        "vehicle_type": provider["vehicle_type"],
        "capacity_kg": provider["capacity_kg"],
        "base_cost": provider["base_cost"],
        "cost_per_km": provider["cost_per_km"],
        "transport_cost": round(transport_cost, 2),
    }


def calculate_price_intelligence(
    quantity_kg: float,
    buyer_price_per_kg: float,
    farmer_expected_price_per_kg: float,
    distance_km: float,
    logistics_df: pd.DataFrame,
    market_modal_price: Optional[Union[float, int, Dict[str, Any]]] = None,
    commodity: Optional[str] = None,
    district: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Calculate comprehensive price intelligence clearly separating:
    1. Mandi Market Benchmark (from data.gov.in)
    2. Buyer Offer (direct contract gross value)
    3. Logistics Cost (vehicle dispatch & freight)
    4. Net Realization (farmer net in hand after logistics)

    Parameters:
        quantity_kg: Volume of produce in kilograms
        buyer_price_per_kg: Offered price per kg by buyer
        farmer_expected_price_per_kg: Farmer's minimum acceptable price
        distance_km: Transit distance from farm to buyer location
        logistics_df: Fleet rate table
        market_modal_price: Benchmark price (float) or benchmark dictionary
        commodity: Optional crop name for auto-benchmark lookup
        district: Optional district for auto-benchmark lookup

    Returns:
        Structured price intelligence dictionary.
    """
    gross_value = float(quantity_kg) * float(buyer_price_per_kg)

    logistics = calculate_logistics_cost(
        distance_km=distance_km,
        quantity_kg=quantity_kg,
        logistics_df=logistics_df,
    )

    transport_cost = logistics["transport_cost"]
    net_realization = max(0.0, gross_value - transport_cost)

    effective_price_per_kg = (
        net_realization / float(quantity_kg)
        if quantity_kg > 0
        else 0.0
    )

    # Resolve benchmark details
    benchmark_info: Optional[Dict[str, Any]] = None
    numeric_modal: Optional[float] = None

    if isinstance(market_modal_price, dict):
        benchmark_info = market_modal_price
        numeric_modal = float(benchmark_info.get("modal_price_per_kg", 0.0))
    elif market_modal_price is not None:
        numeric_modal = float(market_modal_price)
    elif commodity:
        benchmark_info = get_mandi_market_benchmark(commodity=commodity, district=district)
        numeric_modal = float(benchmark_info["modal_price_per_kg"])

    comparison = None
    if numeric_modal is not None and numeric_modal > 0:
        comparison = effective_price_per_kg - numeric_modal

    return {
        "quantity_kg": quantity_kg,
        "buyer_price_per_kg": round(float(buyer_price_per_kg), 2),
        "farmer_expected_price_per_kg": round(float(farmer_expected_price_per_kg), 2),
        "gross_value": round(gross_value, 2),
        "transport_cost": round(transport_cost, 2),
        "net_realization": round(net_realization, 2),
        "effective_price_per_kg": round(effective_price_per_kg, 2),
        "market_modal_price": round(numeric_modal, 2) if numeric_modal is not None else None,
        "comparison_with_market": (
            round(comparison, 2)
            if comparison is not None
            else None
        ),
        "market_benchmark": benchmark_info,
        "logistics_provider": logistics["provider_name"],
        "vehicle_type": logistics["vehicle_type"],
    }