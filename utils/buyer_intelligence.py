"""
Buyer Intelligence Decision-Support Engine | Kisan Setu
Theme: 'Bharat, Reimagined'

Synthesizes multiple procurement intelligence layers for buyers:
1. Algorithmic Match Score
2. Farmer Lot Parameters (Crop, Quantity, Quality Grade, Expected Price, Location)
3. Requirement Fill Percentage (capped at 100%)
4. Live Mandi Modal Benchmark & Comparative Price Differential
5. Market Context Classification ('Below mandi benchmark', 'Near mandi benchmark', 'Above mandi benchmark')
6. Regional ML Demand Signal
7. Logistics Overhead & Delivery Distance

Provides factual, transparent decision support for institutional and commercial buyers
without biased superlatives or speculative claims.
"""

import pandas as pd
import numpy as np


def calculate_buyer_intelligence(
    produce_lot,
    buyer_requirement,
    mandi_benchmark=None,
    demand_forecast=None,
    logistics=None,
    custom_distance_km=None,
    custom_logistics_cost=None,
    match_score=None,
):
    """
    Synthesizes buyer requirement with a matched farmer produce lot and live market telemetry.

    Parameters:
        produce_lot (dict or pd.Series): Farmer produce lot details.
        buyer_requirement (dict or pd.Series): Buyer procurement requirement.
        mandi_benchmark (dict or pd.Series, optional): Mandi market benchmark.
        demand_forecast (dict, optional): Regional demand forecast data.
        logistics (dict or pd.Series, optional): Logistics rate parameters.
        custom_distance_km (float, optional): Direct distance override in km.
        custom_logistics_cost (float, optional): Direct logistics cost override.
        match_score (int or float, optional): Pre-computed match score.

    Returns:
        dict: Structured buyer decision-support intelligence.
    """
    # ---------------------------------------------------------
    # 1. PARSE PRODUCE LOT
    # ---------------------------------------------------------
    if produce_lot is None:
        produce_lot = {}
    elif isinstance(produce_lot, pd.Series):
        produce_lot = produce_lot.to_dict()

    produce_id = str(produce_lot.get("produce_id", ""))
    farmer_id = str(produce_lot.get("farmer_id", ""))
    farmer_name = str(produce_lot.get("farmer_name", f"Farmer {farmer_id}" if farmer_id else "Farmer"))
    crop = str(produce_lot.get("crop", "Produce"))
    farmer_dist = str(produce_lot.get("district", "Nashik"))
    farmer_loc = str(produce_lot.get("location", farmer_dist))
    farmer_grade = str(produce_lot.get("quality_grade", produce_lot.get("grade", "FAQ")))

    try:
        available_qty = float(produce_lot.get("quantity_kg", 0.0))
        if available_qty < 0:
            available_qty = 0.0
    except (ValueError, TypeError):
        available_qty = 0.0

    try:
        farmer_expected_price = float(produce_lot.get("expected_price_per_kg", 0.0))
    except (ValueError, TypeError):
        farmer_expected_price = 0.0

    # ---------------------------------------------------------
    # 2. PARSE BUYER REQUIREMENT
    # ---------------------------------------------------------
    if buyer_requirement is None:
        buyer_requirement = {}
    elif isinstance(buyer_requirement, pd.Series):
        buyer_requirement = buyer_requirement.to_dict()

    buyer_id = str(buyer_requirement.get("buyer_id", ""))
    buyer_name = str(buyer_requirement.get("name", buyer_requirement.get("buyer_name", "Buyer")))
    buyer_dist = str(buyer_requirement.get("district", "Pune"))
    buyer_loc = str(buyer_requirement.get("location", buyer_dist))
    buyer_min_qual = str(buyer_requirement.get("min_quality", "A"))

    try:
        required_qty = float(buyer_requirement.get("required_quantity_kg", 0.0))
        if required_qty < 0:
            required_qty = 0.0
    except (ValueError, TypeError):
        required_qty = 0.0

    try:
        buyer_max_price = float(buyer_requirement.get("max_price_per_kg", 0.0))
    except (ValueError, TypeError):
        buyer_max_price = 0.0

    # ---------------------------------------------------------
    # 3. REQUIREMENT FILL PERCENTAGE (Capped at 100%)
    # ---------------------------------------------------------
    if required_qty > 0 and available_qty > 0:
        raw_fill = (available_qty / required_qty) * 100.0
        fill_percentage = min(100.0, round(raw_fill, 1))
    else:
        fill_percentage = 0.0

    # ---------------------------------------------------------
    # 4. PARSE MANDI BENCHMARK
    # ---------------------------------------------------------
    if mandi_benchmark is None:
        mandi_benchmark = {}
    elif isinstance(mandi_benchmark, pd.Series):
        mandi_benchmark = mandi_benchmark.to_dict()

    mandi_modal_price = None
    for m_key in ["modal_price_per_kg", "modal_price", "latest_modal_price"]:
        if m_key in mandi_benchmark and mandi_benchmark[m_key] is not None:
            try:
                raw_m = float(mandi_benchmark[m_key])
                mandi_modal_price = (raw_m / 100.0) if raw_m > 100.0 else raw_m
                break
            except (ValueError, TypeError):
                pass

    mandi_market = str(mandi_benchmark.get("market", f"{buyer_dist} APMC"))
    mandi_is_live = bool(mandi_benchmark.get("is_live", False))

    # ---------------------------------------------------------
    # 5. COMPARATIVE PRICE DIFFERENTIAL & MARKET CONTEXT
    # ---------------------------------------------------------
    if farmer_expected_price > 0 and mandi_modal_price is not None:
        price_diff = round(farmer_expected_price - mandi_modal_price, 2)
        if price_diff < -0.50:
            market_context = "Below mandi benchmark"
        elif price_diff > 0.50:
            market_context = "Above mandi benchmark"
        else:
            market_context = "Near mandi benchmark"
    else:
        price_diff = None
        market_context = "Mandi benchmark unavailable"

    # ---------------------------------------------------------
    # 6. DISTANCE & LOGISTICS
    # ---------------------------------------------------------
    if custom_distance_km is not None:
        try:
            distance_km = max(0.0, float(custom_distance_km))
        except (ValueError, TypeError):
            distance_km = 0.0
    else:
        try:
            distance_km = float(produce_lot.get("distance_km", 0.0))
        except (ValueError, TypeError):
            distance_km = 0.0

    if custom_logistics_cost is not None:
        try:
            logistics_cost = max(0.0, float(custom_logistics_cost))
        except (ValueError, TypeError):
            logistics_cost = 0.0
    else:
        if logistics is not None:
            if isinstance(logistics, pd.Series):
                logistics = logistics.to_dict()
            cost_per_km = float(logistics.get("cost_per_km", 4.5))
            base_cost = float(logistics.get("base_cost", 300.0))
        else:
            cost_per_km = 4.5
            base_cost = 300.0

        if distance_km > 0:
            logistics_cost = round(base_cost + (distance_km * cost_per_km), 2)
        else:
            logistics_cost = 0.0

    # ---------------------------------------------------------
    # 7. DEMAND SIGNAL
    # ---------------------------------------------------------
    if demand_forecast is None:
        demand_forecast = {}

    demand_trend = str(demand_forecast.get("trend", "Unavailable"))
    if demand_trend not in {"Increasing", "Stable", "Decreasing"}:
        demand_trend = "Unavailable"

    demand_source = str(demand_forecast.get("demand_source", "Unavailable" if demand_trend == "Unavailable" else "Platform transaction history"))
    
    demand_pct_change = None
    if demand_forecast and "percentage_change" in demand_forecast and demand_forecast["percentage_change"] is not None:
        try:
            demand_pct_change = float(demand_forecast["percentage_change"])
        except (ValueError, TypeError):
            demand_pct_change = None

    # ---------------------------------------------------------
    # 8. RESOLVE MATCH SCORE
    # ---------------------------------------------------------
    if match_score is not None:
        try:
            resolved_score = int(float(match_score))
        except (ValueError, TypeError):
            resolved_score = 0
    else:
        try:
            resolved_score = int(float(produce_lot.get("match_score", 0)))
        except (ValueError, TypeError):
            resolved_score = 0

    # ---------------------------------------------------------
    # 9. FACTUAL EXPLANATION
    # ---------------------------------------------------------
    explanation_parts = []
    
    if required_qty > 0 and available_qty > 0:
        explanation_parts.append(
            f"This lot provides {available_qty:,.0f} kg against a requirement of {required_qty:,.0f} kg "
            f"({fill_percentage:.1f}% quantity coverage)."
        )
    elif available_qty > 0:
        explanation_parts.append(f"This lot provides {available_qty:,.0f} kg.")

    if farmer_expected_price > 0 and mandi_modal_price is not None:
        explanation_parts.append(
            f"The expected price is ₹{farmer_expected_price:.2f}/kg compared with the live mandi modal benchmark of "
            f"₹{mandi_modal_price:.2f}/kg ({market_context.lower()})."
        )
    elif farmer_expected_price > 0:
        explanation_parts.append(f"The expected price is ₹{farmer_expected_price:.2f}/kg.")

    if demand_trend != "Unavailable":
        sign = "+" if (demand_pct_change or 0) >= 0 else ""
        pct_txt = f" ({sign}{demand_pct_change:.1f}%)" if demand_pct_change is not None else ""
        explanation_parts.append(f"Regional demand momentum is currently {demand_trend}{pct_txt}.")

    if not explanation_parts:
        explanation_text = "Buyer intelligence parameters will update as procurement criteria are selected."
    else:
        explanation_text = " ".join(explanation_parts)

    # ---------------------------------------------------------
    # 10. RETURN STRUCTURED INTELLIGENCE
    # ---------------------------------------------------------
    return {
        "produce_id": produce_id,
        "farmer_id": farmer_id,
        "farmer_name": farmer_name,
        "crop": crop,
        "farmer_location": f"{farmer_loc}, {farmer_dist}" if farmer_loc != farmer_dist else farmer_dist,
        "farmer_district": farmer_dist,
        "available_quantity_kg": available_qty,
        "quality_grade": farmer_grade,
        "farmer_expected_price_per_kg": farmer_expected_price,
        "buyer_id": buyer_id,
        "buyer_name": buyer_name,
        "buyer_required_quantity_kg": required_qty,
        "buyer_max_price_per_kg": buyer_max_price,
        "buyer_min_quality": buyer_min_qual,
        "match_score": resolved_score,
        "fill_percentage": fill_percentage,
        "mandi_modal_price_per_kg": mandi_modal_price,
        "mandi_market": mandi_market,
        "mandi_is_live": mandi_is_live,
        "price_difference_vs_mandi": price_diff,
        "market_context": market_context,
        "distance_km": distance_km,
        "logistics_cost": logistics_cost,
        "demand_signal": demand_trend,
        "demand_source": demand_source,
        "demand_percentage_change": demand_pct_change,
        "explanation": explanation_text,
    }
