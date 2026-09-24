"""
Comprehensive test suite for the upgraded Kisan Setu Demand Forecasting Module.
"""
import sys
import os
import pandas as pd
import numpy as np

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai.demand_forecasting import forecast_demand, forecast_demand_with_market_context


def run_all_tests():
    print("=" * 70)
    print("RUNNING DEMAND FORECASTING UPGRADE TEST SUITE")
    print("=" * 70)

    # 1. Load actual dataset
    demand_path = os.path.join("data", "demand.csv")
    demand_df = pd.read_csv(demand_path)
    print(f"Loaded {demand_path} with {len(demand_df)} rows:\n{demand_df}\n")

    # TEST A: Pune + Onion (3-day forecast)
    print("-" * 50)
    print("TEST 1: Pune + Onion (3-Day Forecast)")
    fc_pune_onion_3 = forecast_demand(demand_df, "Pune", "Onion", forecast_days=3)
    assert fc_pune_onion_3 is not None, "Failed: fc_pune_onion_3 returned None"
    assert fc_pune_onion_3["district"] == "Pune"
    assert fc_pune_onion_3["crop"] == "Onion"
    assert len(fc_pune_onion_3["forecast_values"]) == 3
    assert fc_pune_onion_3["trend"] == "Increasing"
    assert fc_pune_onion_3["data_quality"] == "Moderate" # 6 days
    assert fc_pune_onion_3["history_days"] == 6
    assert "explanation" in fc_pune_onion_3
    print("Result:")
    for k, v in fc_pune_onion_3.items():
        if k != "historical_data":
            print(f"  {k}: {v}")
    print("[PASSED] Test 1")

    # TEST B: Pune + Tomato (7-day forecast)
    print("-" * 50)
    print("TEST 2: Pune + Tomato (7-Day Forecast)")
    fc_pune_tomato_7 = forecast_demand(demand_df, "Pune", "Tomato", forecast_days=7)
    assert fc_pune_tomato_7 is not None
    assert len(fc_pune_tomato_7["forecast_values"]) == 7
    assert fc_pune_tomato_7["trend"] == "Increasing"
    assert fc_pune_tomato_7["history_days"] == 6
    print("Result:")
    for k, v in fc_pune_tomato_7.items():
        if k != "historical_data":
            print(f"  {k}: {v}")
    print("[PASSED] Test 2 Passed")

    # TEST C: Nonexistent Crop
    print("-" * 50)
    print("TEST 3: Nonexistent Crop ('DragonFruit')")
    fc_nonexistent_crop = forecast_demand(demand_df, "Pune", "DragonFruit", forecast_days=3)
    assert fc_nonexistent_crop is None, "Failed: Nonexistent crop should return None"
    print("[PASSED] Test 3 Passed: Correctly returned None")

    # TEST D: Nonexistent District
    print("-" * 50)
    print("TEST 4: Nonexistent District ('Atlantis')")
    fc_nonexistent_dist = forecast_demand(demand_df, "Atlantis", "Onion", forecast_days=3)
    assert fc_nonexistent_dist is None, "Failed: Nonexistent district should return None"
    print("[PASSED] Test 4 Passed: Correctly returned None")

    # TEST E: Insufficient History (<3 observations)
    print("-" * 50)
    print("TEST 5: Insufficient History (2 rows)")
    small_df = pd.DataFrame([
        {"date": "2026-09-01", "district": "Pune", "crop": "Wheat", "demand_quantity_kg": 100, "orders": 1},
        {"date": "2026-09-02", "district": "Pune", "crop": "Wheat", "demand_quantity_kg": 110, "orders": 2},
    ])
    fc_insufficient = forecast_demand(small_df, "Pune", "Wheat", forecast_days=3)
    assert fc_insufficient is None, "Failed: Insufficient data (<3) should return None"
    print("[PASSED] Test 5 Passed: Correctly returned None")

    # TEST F: Empty / Invalid Inputs
    print("-" * 50)
    print("TEST 6: Invalid & Empty Inputs Handling")
    assert forecast_demand(None, "Pune", "Onion") is None
    assert forecast_demand(pd.DataFrame(), "Pune", "Onion") is None
    assert forecast_demand(demand_df, "", "Onion") is None
    assert forecast_demand(demand_df, "Pune", "") is None
    assert forecast_demand(demand_df[["district", "crop"]], "Pune", "Onion") is None # missing required cols
    print("[PASSED] Test 6 Passed: All malformed inputs safely handled")

    # TEST G: Trend Classification (Decreasing & Stable verification)
    print("-" * 50)
    print("TEST 7: Adaptive Relative Trend Classification (Decreasing & Stable)")
    # Decreasing dataset
    dec_df = pd.DataFrame([
        {"date": f"2026-09-0{i}", "district": "Nashik", "crop": "Potato", "demand_quantity_kg": 5000 - i * 400, "orders": 30 - i * 2}
        for i in range(1, 6)
    ])
    fc_dec = forecast_demand(dec_df, "Nashik", "Potato", forecast_days=3)
    assert fc_dec is not None
    assert fc_dec["trend"] == "Decreasing"
    assert fc_dec["percentage_change"] < 0
    print(f"  Decreasing trend result: trend={fc_dec['trend']}, %change={fc_dec['percentage_change']}%")

    # Stable dataset
    stable_df = pd.DataFrame([
        {"date": f"2026-09-0{i}", "district": "Nashik", "crop": "Carrot", "demand_quantity_kg": 2000 + (i % 2) * 5, "orders": 10}
        for i in range(1, 6)
    ])
    fc_stable = forecast_demand(stable_df, "Nashik", "Carrot", forecast_days=3)
    assert fc_stable is not None
    assert fc_stable["trend"] == "Stable"
    print(f"  Stable trend result: trend={fc_stable['trend']}, %change={fc_stable['percentage_change']}%")
    print("[PASSED] Test 7 Passed: Scale-relative trend accurately classified")

    # TEST H: Data Quality Categories (Limited vs Moderate vs Good)
    print("-" * 50)
    print("TEST 8: Data Quality Indicator")
    # 3 days = Limited
    lim_df = dec_df.iloc[:3]
    fc_lim = forecast_demand(lim_df, "Nashik", "Potato", 3)
    assert fc_lim["data_quality"] == "Limited"
    assert fc_lim["history_days"] == 3

    # 6 days = Moderate
    assert fc_pune_onion_3["data_quality"] == "Moderate"

    # 15 days = Good
    good_df = pd.DataFrame([
        {"date": f"2026-09-{i:02d}", "district": "Nagpur", "crop": "Orange", "demand_quantity_kg": 1000 + i * 10, "orders": 5 + i}
        for i in range(1, 16)
    ])
    fc_good = forecast_demand(good_df, "Nagpur", "Orange", 3)
    assert fc_good["data_quality"] == "Good"
    assert fc_good["history_days"] == 15
    print("[PASSED] Test 8 Passed: Limited, Moderate, Good data quality calculated properly")

    # TEST I: Orders without variation (Zero Variance Safety)
    print("-" * 50)
    print("TEST 9: Orders without variation handling")
    const_orders_df = pd.DataFrame([
        {"date": f"2026-09-0{i}", "district": "Pune", "crop": "Garlic", "demand_quantity_kg": 500 + i * 50, "orders": 5} # all 5
        for i in range(1, 6)
    ])
    fc_const_orders = forecast_demand(const_orders_df, "Pune", "Garlic", 3)
    assert fc_const_orders is not None
    assert fc_const_orders["trend"] == "Increasing"
    print("[PASSED] Test 9 Passed: Zero variation orders safely fallen back to single-feature baseline")

    # TEST J: Market Context Integration & Unit Check
    print("-" * 50)
    print("TEST 10: Market Context Integration with modal_price_per_kg & modal_price")
    market_df_norm = pd.DataFrame([
        {"commodity": "Onion", "market": "Pune APMC", "modal_price_per_kg": 34.50, "arrival_date": "2026-09-24"},
        {"commodity": "Onion", "market": "Pimpalgaon", "modal_price_per_kg": 43.00, "arrival_date": "2026-09-24"},
    ])
    fc_with_mkt = forecast_demand_with_market_context(
        demand_df=demand_df,
        district="Pune",
        crop="Onion",
        forecast_days=3,
        market_prices_df=market_df_norm
    )
    assert fc_with_mkt is not None
    assert "market_price_context" in fc_with_mkt
    mkt_ctx = fc_with_mkt["market_price_context"]
    assert mkt_ctx["latest_modal_price_per_kg"] == 43.00, f"Expected 43.00, got {mkt_ctx['latest_modal_price_per_kg']} (checked no double division)"
    assert mkt_ctx["mandi_records_count"] == 2
    print(f"  Market Context: {mkt_ctx}")

    # Fallback to modal_price in Quintals
    market_df_quintal = pd.DataFrame([
        {"crop": "Tomato", "market": "Ghoti", "modal_price": 2100.0, "arrival_date": "2026-09-24"}
    ])
    fc_with_mkt2 = forecast_demand_with_market_context(
        demand_df=demand_df,
        district="Pune",
        crop="Tomato",
        forecast_days=3,
        market_prices_df=market_df_quintal
    )
    assert fc_with_mkt2["market_price_context"]["latest_modal_price_per_kg"] == 21.00
    print("[PASSED] Test 10 Passed: Market context correctly extracted without double division")

    # TEST K: Streamlit Pages Compatibility
    print("-" * 50)
    print("TEST 11: Import and Compatibility Check with Streamlit Pages")
    from pages import farmer, buyer, digital_mandi, logistics, consumer
    from ai import matching, pricing
    print("[PASSED] Test 11 Passed: All pages and AI modules imported cleanly")

    print("=" * 70)
    print("ALL DEMAND FORECASTING TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


def test_demand_forecasting_upgrade():
    """Pytest test wrapper for demand forecasting upgrade suite."""
    run_all_tests()


if __name__ == "__main__":
    run_all_tests()

