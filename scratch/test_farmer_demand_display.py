"""
Verification script for Farmer Decision Hub Demand Outlook Display Integration.
"""
import sys
import os
import pandas as pd

# Add repository root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.data_loader import load_demand, load_produce, load_buyers, load_prices, load_transactions
from ai.matching import find_matches
from ai.demand_forecasting import forecast_demand_with_market_context
from ai.pricing import get_mandi_market_benchmark


def test_farmer_demand_integration():
    print("=" * 70)
    print("TESTING FARMER DECISION HUB DEMAND OUTLOOK DISPLAY INTEGRATION")
    print("=" * 70)

    # 1. Load datasets
    demand_df = load_demand()
    produce_df = load_produce()
    buyers_df = load_buyers()
    prices_df = load_prices()

    print(f"Loaded: demand={len(demand_df)}, produce={len(produce_df)}, buyers={len(buyers_df)}, prices={len(prices_df)}")

    # 2. Test Pune + Onion
    print("\n--- TEST 1: Pune + Onion (3-Day and 7-Day) ---")
    fc_pune_onion_3 = forecast_demand_with_market_context(
        demand_df=demand_df,
        district="Pune",
        crop="Onion",
        forecast_days=3,
        market_prices_df=prices_df
    )
    assert fc_pune_onion_3 is not None, "Failed: Pune Onion forecast should not be None"
    assert fc_pune_onion_3["district"] == "Pune"
    assert fc_pune_onion_3["crop"] == "Onion"
    assert fc_pune_onion_3["current_demand_kg"] == 4300.0
    assert fc_pune_onion_3["forecast_demand_kg"] == 4748.0
    assert len(fc_pune_onion_3["forecast_values"]) == 3
    assert fc_pune_onion_3["trend"] == "Increasing"
    assert fc_pune_onion_3["percentage_change"] == 10.4
    assert fc_pune_onion_3["history_days"] == 6
    assert fc_pune_onion_3["data_quality"] == "Moderate"
    assert "market_price_context" in fc_pune_onion_3
    print("Pune Onion 3-Day Result:")
    for k, v in fc_pune_onion_3.items():
        if k != "historical_data":
            print(f"  {k}: {v}")
    print("[PASSED] Test 1: Pune + Onion 3-day forecast valid")

    # 3. Test Pune + Tomato
    print("\n--- TEST 2: Pune + Tomato (7-Day) ---")
    fc_pune_tomato_7 = forecast_demand_with_market_context(
        demand_df=demand_df,
        district="Pune",
        crop="Tomato",
        forecast_days=7,
        market_prices_df=prices_df
    )
    assert fc_pune_tomato_7 is not None
    assert len(fc_pune_tomato_7["forecast_values"]) == 7
    assert fc_pune_tomato_7["current_demand_kg"] == 2600.0
    assert fc_pune_tomato_7["forecast_demand_kg"] == 3205.0
    assert fc_pune_tomato_7["trend"] == "Increasing"
    assert fc_pune_tomato_7["percentage_change"] == 23.3
    print("Pune Tomato 7-Day Result:")
    for k, v in fc_pune_tomato_7.items():
        if k != "historical_data":
            print(f"  {k}: {v}")
    print("[PASSED] Test 2: Pune + Tomato 7-day forecast valid")

    # 4. Test Regional Demand Series Hierarchy (Nashik + Onion -> Platform Transactions)
    print("\n--- TEST 3: Nashik + Onion (Transaction Fallback) ---")
    from utils.demand_data import get_regional_demand_series
    active_df, src_label = get_regional_demand_series("Nashik", "Onion", demand_df, transactions_df=load_transactions(), produce_df=produce_df)
    assert active_df is not None, "Nashik Onion should resolve from transactions"
    assert src_label == "Platform transaction history"
    fc_nashik_onion = forecast_demand_with_market_context(
        demand_df=active_df,
        district="Nashik",
        crop="Onion",
        forecast_days=3,
        market_prices_df=prices_df
    )
    assert fc_nashik_onion is not None
    assert fc_nashik_onion["history_days"] == 3
    assert fc_nashik_onion["data_quality"] == "Limited"
    print(f"Nashik Onion Result from {src_label}: {fc_nashik_onion['forecast_demand_kg']} kg (Quality: {fc_nashik_onion['data_quality']})")
    print("[PASSED] Test 3: Transaction fallback hierarchy for Nashik Onion verified")

    # 5. Verify Buyer Matching with and without forecast_kg
    print("\n--- TEST 4: Buyer Matching Integration ---")
    sample_lot = produce_df.iloc[0] # P001 (Onion, Niphad, Nashik)
    
    # Case A: with forecast_kg from Pune (4748 kg)
    matches_with_fc = find_matches(sample_lot, buyers_df, forecast_demand=4748.0)
    assert not matches_with_fc.empty
    assert "match_score" in matches_with_fc.columns

    # Case B: with forecast_kg = None (when district not in demand series)
    matches_without_fc = find_matches(sample_lot, buyers_df, forecast_demand=None)
    assert not matches_without_fc.empty
    assert "match_score" in matches_without_fc.columns
    print(f"Matches found with forecast: {len(matches_with_fc)}, top score: {matches_with_fc.iloc[0]['match_score']}%")
    print(f"Matches found without forecast: {len(matches_without_fc)}, top score: {matches_without_fc.iloc[0]['match_score']}%")
    print("[PASSED] Test 4: Buyer matching behaves robustly with both available and None forecast")

    # 6. Verify Mandi Benchmark separation
    print("\n--- TEST 5: Mandi Benchmark Separation ---")
    mandi_bench = get_mandi_market_benchmark("Onion", "Nashik", "Maharashtra")
    assert "modal_price_per_kg" in mandi_bench
    assert mandi_bench["modal_price_per_kg"] > 0
    print(f"Mandi Benchmark: {mandi_bench['modal_price_per_kg']} Rs/kg (Market: {mandi_bench.get('market')})")
    print("[PASSED] Test 5: Mandi benchmark cleanly isolated from demand quantities")

    # 7. Verify Page Imports & Compatibility
    print("\n--- TEST 6: Page Imports & Full Application Compatibility ---")
    from pages import farmer, buyer, digital_mandi, logistics, consumer
    print("[PASSED] Test 6: All pages imported cleanly without error")

    print("\n" + "=" * 70)
    print("ALL FARMER DEMAND OUTLOOK DISPLAY TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_farmer_demand_integration()
