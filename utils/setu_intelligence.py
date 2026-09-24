"""
Setu Intelligence Decision-Support Engine | Kisan Setu
Theme: 'Bharat, Reimagined'

Synthesizes multiple intelligence layers:
1. Live Mandi Benchmark (data.gov.in / AGMARKNET)
2. Farmer's Produce Lot Details
3. Direct Buyer Match Opportunity
4. ML Demand Forecast & Momentum
5. Logistics Cost & Net Realization

Provides actionable, factual decision support without making speculative
or guaranteed profit claims.
"""
import pandas as pd
import numpy as np


def calculate_setu_intelligence(
    produce_lot,
    mandi_benchmark=None,
    buyer_match=None,
    demand_forecast=None,
    logistics=None,
    custom_logistics_cost=None
):
    """
    Synthesizes farmer lot, buyer match, live mandi benchmark, demand forecast,
    and logistics parameters to produce a unified decision-support assessment.

    Parameters:
        produce_lot (dict or pd.Series): Selected produce lot parameters.
        mandi_benchmark (dict or pd.Series, optional): Mandi market benchmark.
        buyer_match (dict or pd.Series, optional): Selected buyer match details.
        demand_forecast (dict, optional): Demand forecasting payload.
        logistics (dict or pd.Series, optional): Logistics rate parameters.
        custom_logistics_cost (float, optional): Direct logistics cost override.

    Returns:
        dict: Structured decision-support intelligence.
    """
    # ---------------------------------------------------------
    # 1. PARSE PRODUCE LOT
    # ---------------------------------------------------------
    if produce_lot is None:
        produce_lot = {}
    elif isinstance(produce_lot, pd.Series):
        produce_lot = produce_lot.to_dict()

    crop = str(produce_lot.get("crop", "Produce"))
    district = str(produce_lot.get("district", "Regional"))
    location = str(produce_lot.get("location", district))
    grade = str(produce_lot.get("quality_grade", "FAQ"))

    try:
        quantity_kg = float(produce_lot.get("quantity_kg", 0.0))
        if quantity_kg < 0:
            quantity_kg = 0.0
    except (ValueError, TypeError):
        quantity_kg = 0.0

    try:
        expected_price_per_kg = float(produce_lot.get("expected_price_per_kg", 0.0))
    except (ValueError, TypeError):
        expected_price_per_kg = 0.0

    # ---------------------------------------------------------
    # 2. PARSE BUYER MATCH
    # ---------------------------------------------------------
    if buyer_match is None:
        buyer_match = {}
    elif isinstance(buyer_match, pd.Series):
        buyer_match = buyer_match.to_dict()

    buyer_id = str(buyer_match.get("buyer_id", ""))
    buyer_name = str(buyer_match.get("buyer_name", buyer_match.get("name", "")))
    buyer_type = str(buyer_match.get("buyer_type", "Wholesaler"))
    buyer_loc = str(buyer_match.get("location", buyer_match.get("district", "Regional Hub")))
    
    try:
        match_score = int(float(buyer_match.get("match_score", 0)))
    except (ValueError, TypeError):
        match_score = None

    buyer_offer_price = None
    for p_key in ["max_price_per_kg", "price_per_kg", "buyer_offer_price", "price"]:
        if p_key in buyer_match and buyer_match[p_key] is not None:
            try:
                buyer_offer_price = float(buyer_match[p_key])
                break
            except (ValueError, TypeError):
                pass

    try:
        buyer_req_qty = float(buyer_match.get("required_quantity_kg", 0.0))
    except (ValueError, TypeError):
        buyer_req_qty = None

    try:
        distance_km = float(buyer_match.get("distance_km", 0.0))
    except (ValueError, TypeError):
        distance_km = 0.0

    # ---------------------------------------------------------
    # 3. PARSE MANDI BENCHMARK
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

    mandi_min_price = None
    if "min_price_per_kg" in mandi_benchmark and mandi_benchmark["min_price_per_kg"] is not None:
        try:
            mandi_min_price = float(mandi_benchmark["min_price_per_kg"])
        except (ValueError, TypeError):
            mandi_min_price = mandi_modal_price
    else:
        mandi_min_price = mandi_modal_price

    mandi_max_price = None
    if "max_price_per_kg" in mandi_benchmark and mandi_benchmark["max_price_per_kg"] is not None:
        try:
            mandi_max_price = float(mandi_benchmark["max_price_per_kg"])
        except (ValueError, TypeError):
            mandi_max_price = mandi_modal_price
    else:
        mandi_max_price = mandi_modal_price

    mandi_market = str(mandi_benchmark.get("market", f"{district} APMC"))
    mandi_is_live = bool(mandi_benchmark.get("is_live", False))

    # ---------------------------------------------------------
    # 4. PARSE DEMAND FORECAST
    # ---------------------------------------------------------
    if demand_forecast is None:
        demand_forecast = {}

    demand_trend = str(demand_forecast.get("trend", "Unavailable"))
    if demand_trend not in {"Increasing", "Stable", "Decreasing"}:
        demand_trend = "Unavailable"

    demand_source = str(demand_forecast.get("demand_source", "Unavailable" if demand_trend == "Unavailable" else "Platform transaction history"))
    
    try:
        forecast_demand_kg = float(demand_forecast.get("forecast_demand_kg", 0.0))
    except (ValueError, TypeError):
        forecast_demand_kg = None

    try:
        demand_pct_change = float(demand_forecast.get("percentage_change", 0.0))
    except (ValueError, TypeError):
        demand_pct_change = None

    data_quality = str(demand_forecast.get("data_quality", "Limited"))
    history_days = int(demand_forecast.get("history_days", 0))

    # ---------------------------------------------------------
    # 5. LOGISTICS COST CALCULATION
    # ---------------------------------------------------------
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
    # 6. FINANCIAL REALIZATIONS & SPREADS
    # ---------------------------------------------------------
    # Buyer gross & net
    if buyer_offer_price is not None and quantity_kg > 0:
        buyer_gross_value = round(buyer_offer_price * quantity_kg, 2)
        estimated_net_realization = round(max(0.0, buyer_gross_value - logistics_cost), 2)
        effective_net_per_kg = round(estimated_net_realization / quantity_kg, 2)
    else:
        buyer_gross_value = 0.0
        estimated_net_realization = 0.0
        effective_net_per_kg = 0.0

    # Mandi benchmark gross & net (net of logistics)
    if mandi_modal_price is not None and quantity_kg > 0:
        mandi_benchmark_gross_value = round(mandi_modal_price * quantity_kg, 2)
        mandi_net_realization = round(max(0.0, mandi_benchmark_gross_value - logistics_cost), 2)
        mandi_benchmark_net_value = mandi_net_realization
    else:
        mandi_benchmark_gross_value = None
        mandi_net_realization = None
        mandi_benchmark_net_value = None

    # Comparison metrics
    if buyer_offer_price is not None and mandi_modal_price is not None:
        price_spread_per_kg = round(buyer_offer_price - mandi_modal_price, 2)
    else:
        price_spread_per_kg = None

    if buyer_offer_price is not None and mandi_net_realization is not None:
        net_difference = round(estimated_net_realization - mandi_net_realization, 2)
    else:
        net_difference = None

    # ---------------------------------------------------------
    # 7. DECISION FACTORS COMPILATION
    # ---------------------------------------------------------
    decision_factors = {}

    # Factor 1: Price vs Mandi
    if price_spread_per_kg is not None:
        sign = "+" if price_spread_per_kg >= 0 else ""
        decision_factors["price_vs_mandi"] = (
            f"{sign}₹{price_spread_per_kg:.2f}/kg over Mandi Modal Benchmark "
            f"({buyer_name or 'Buyer'} @ ₹{buyer_offer_price:.2f}/kg vs {mandi_market} @ ₹{mandi_modal_price:.2f}/kg)"
        )
    else:
        decision_factors["price_vs_mandi"] = "Mandi modal benchmark or buyer offer unavailable for direct price comparison."

    # Factor 2: Demand Outlook
    if demand_trend != "Unavailable":
        sign = "+" if (demand_pct_change or 0) >= 0 else ""
        pct_str = f" ({sign}{demand_pct_change:.1f}%)" if demand_pct_change is not None else ""
        decision_factors["demand_outlook"] = (
            f"Demand signal is {demand_trend}{pct_str} based on {demand_source} ({history_days}d history, {data_quality} quality)."
        )
    else:
        decision_factors["demand_outlook"] = "Regional demand forecast currently unavailable due to insufficient historical observations."

    # Factor 3: Logistics Impact
    if quantity_kg > 0 and logistics_cost > 0:
        freight_per_kg = round(logistics_cost / quantity_kg, 2)
        decision_factors["logistics_impact"] = (
            f"Estimated freight of ₹{logistics_cost:,.0f} (-₹{freight_per_kg:.2f}/kg) across {distance_km:.0f} km "
            f"results in an effective net price of ₹{effective_net_per_kg:.2f}/kg."
        )
    else:
        decision_factors["logistics_impact"] = "Direct farm-gate pickup or local transport with minimal freight overhead."

    # Factor 4: Buyer Match
    if match_score is not None and buyer_name:
        decision_factors["buyer_match"] = f"{match_score}% algorithmic compatibility with {buyer_name} ({buyer_type} in {buyer_loc})."
    else:
        decision_factors["buyer_match"] = "Buyer compatibility evaluation pending selection."

    # Factor 5: Quantity Fit
    if buyer_req_qty is not None and buyer_req_qty > 0 and quantity_kg > 0:
        fill_pct = min(100.0, round((quantity_kg / buyer_req_qty) * 100.0, 1))
        decision_factors["quantity_fit"] = f"{quantity_kg:,.0f} kg lot fulfills {fill_pct:.0f}% of buyer requirement ({buyer_req_qty:,.0f} kg)."
    else:
        decision_factors["quantity_fit"] = f"{quantity_kg:,.0f} kg lot volume available."

    # ---------------------------------------------------------
    # 8. CONCISE FACTUAL EXPLANATION ("Why this matters")
    # ---------------------------------------------------------
    explanation_parts = []

    if buyer_offer_price is not None and mandi_modal_price is not None:
        explanation_parts.append(
            f"Buyer offer is ₹{buyer_offer_price:.2f}/kg compared with the live mandi modal benchmark of ₹{mandi_modal_price:.2f}/kg."
        )
    elif buyer_offer_price is not None:
        explanation_parts.append(f"Buyer offer is ₹{buyer_offer_price:.2f}/kg.")
    elif mandi_modal_price is not None:
        explanation_parts.append(f"Mandi modal benchmark is ₹{mandi_modal_price:.2f}/kg.")

    if buyer_offer_price is not None and quantity_kg > 0:
        explanation_parts.append(
            f"After estimated logistics cost of ₹{logistics_cost:,.0f}, the estimated net realization is ₹{estimated_net_realization:,.0f} "
            f"(₹{effective_net_per_kg:.2f}/kg) for this {quantity_kg:,.0f} kg lot."
        )

    if demand_trend != "Unavailable":
        sign = "+" if (demand_pct_change or 0) >= 0 else ""
        pct_txt = f" ({sign}{demand_pct_change:.1f}%)" if demand_pct_change is not None else ""
        explanation_parts.append(
            f"Platform demand is currently {demand_trend}{pct_txt} based on {demand_source}."
        )

    if not explanation_parts:
        explanation_text = "Decision support metrics will update as market and buyer parameters are selected."
    else:
        explanation_text = " ".join(explanation_parts)

    # ---------------------------------------------------------
    # 9. STRUCTURED RESULT
    # ---------------------------------------------------------
    return {
        "crop": crop,
        "district": district,
        "quantity_kg": quantity_kg,
        "expected_price_per_kg": expected_price_per_kg,
        "buyer_id": buyer_id,
        "buyer_name": buyer_name,
        "buyer_offer_price_per_kg": buyer_offer_price,
        "buyer_gross_value": buyer_gross_value,
        "logistics_cost": logistics_cost,
        "estimated_net_realization": estimated_net_realization,
        "effective_net_per_kg": effective_net_per_kg,
        "mandi_modal_price_per_kg": mandi_modal_price,
        "mandi_min_price_per_kg": mandi_min_price,
        "mandi_max_price_per_kg": mandi_max_price,
        "mandi_market": mandi_market,
        "mandi_is_live": mandi_is_live,
        "mandi_benchmark_gross_value": mandi_benchmark_gross_value,
        "mandi_benchmark_net_value": mandi_benchmark_net_value,
        "mandi_net_realization": mandi_net_realization,
        "price_spread_per_kg": price_spread_per_kg,
        "net_difference": net_difference,
        "demand_signal": demand_trend,
        "demand_source": demand_source,
        "demand_percentage_change": demand_pct_change,
        "forecast_demand_kg": forecast_demand_kg,
        "match_score": match_score,
        "distance_km": distance_km,
        "decision_factors": decision_factors,
        "explanation": explanation_text,
    }
