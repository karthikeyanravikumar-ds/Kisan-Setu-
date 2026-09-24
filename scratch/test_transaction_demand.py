"""
Comprehensive test suite for transaction-derived demand data preparation.
Covers all 14 required verification scenarios.
"""
import sys
import os
import pandas as pd
import numpy as np

# Ensure root directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.demand_data import build_transaction_demand_history, get_regional_demand_series
from utils.data_loader import load_demand, load_produce, load_transactions, load_prices
from ai.demand_forecasting import forecast_demand, forecast_demand_with_market_context


def run_tests():
    print("=" * 70)
    print("RUNNING TRANSACTION-DERIVED DEMAND PREPARATION TEST SUITE")
    print("=" * 70)

    # Load actual datasets
    demand_df_original = load_demand()
    produce_df = load_produce()
    transactions_df = load_transactions()
    prices_df = load_prices()

    print(f"Loaded: demand.csv ({len(demand_df_original)} rows), produce.csv ({len(produce_df)} rows), transactions.csv ({len(transactions_df)} rows)")

    # -------------------------------------------------------------
    # TEST 1, 2, 3: Transactions + Produce Join, Crop & District Mapping
    # -------------------------------------------------------------
    print("\n--- TEST 1, 2, 3: Successful Join, Crop & District Mapping ---")
    derived_df = build_transaction_demand_history(transactions_df, produce_df)
    assert not derived_df.empty, "Derived demand history should not be empty"
    assert set(derived_df.columns) == {"date", "district", "crop", "demand_quantity_kg", "orders"}
    
    # Verify crops and districts present in transactions
    districts = set(derived_df["district"].unique())
    crops = set(derived_df["crop"].unique())
    print(f"Districts in transaction demand: {districts}")
    print(f"Crops in transaction demand: {crops}")
    assert "Nashik" in districts or "Ahmednagar" in districts
    assert "Onion" in crops
    print("[PASSED] Tests 1, 2, 3: Join and metadata mapping successful")

    # -------------------------------------------------------------
    # TEST 4, 5, 6: Date Aggregation, Quantity Sum, and Order Count
    # -------------------------------------------------------------
    print("\n--- TEST 4, 5, 6: Date Aggregation, Quantity Aggregation & Order Count ---")
    # Sample synthetic test with known values
    sample_prod = pd.DataFrame([
        {"produce_id": "P100", "crop": "Onion", "district": "Nashik", "quantity_kg": 1000},
        {"produce_id": "P101", "crop": "Onion", "district": "Nashik", "quantity_kg": 500},
    ])
    sample_tx = pd.DataFrame([
        {"transaction_id": "TX1", "produce_id": "P100", "quantity_kg": 300, "date": "2026-09-01", "status": "Completed"},
        {"transaction_id": "TX2", "produce_id": "P101", "quantity_kg": 200, "date": "2026-09-01", "status": "Confirmed"},
        {"transaction_id": "TX3", "produce_id": "P100", "quantity_kg": 400, "date": "2026-09-02", "status": "In Transit"},
    ])
    agg_res = build_transaction_demand_history(sample_tx, sample_prod)
    assert len(agg_res) == 2, f"Expected 2 aggregated rows for 2 dates, got {len(agg_res)}"
    
    row_day1 = agg_res[agg_res["date"] == "2026-09-01"].iloc[0]
    assert row_day1["demand_quantity_kg"] == 500.0, f"Expected 500 kg, got {row_day1['demand_quantity_kg']}"
    assert row_day1["orders"] == 2, f"Expected 2 orders, got {row_day1['orders']}"
    
    row_day2 = agg_res[agg_res["date"] == "2026-09-02"].iloc[0]
    assert row_day2["demand_quantity_kg"] == 400.0
    assert row_day2["orders"] == 1
    print("[PASSED] Tests 4, 5, 6: Date aggregation, sum quantity, and order count verified")

    # -------------------------------------------------------------
    # TEST 7: Duplicate Transaction Protection
    # -------------------------------------------------------------
    print("\n--- TEST 7: Duplicate Transaction Protection ---")
    dup_tx = pd.DataFrame([
        {"transaction_id": "TX1", "produce_id": "P100", "quantity_kg": 300, "date": "2026-09-01", "status": "Completed"},
        {"transaction_id": "TX1", "produce_id": "P100", "quantity_kg": 300, "date": "2026-09-01", "status": "Completed"}, # duplicate
    ])
    dup_res = build_transaction_demand_history(dup_tx, sample_prod)
    assert len(dup_res) == 1
    assert dup_res.iloc[0]["demand_quantity_kg"] == 300.0, "Duplicate transaction must not be double counted"
    assert dup_res.iloc[0]["orders"] == 1
    print("[PASSED] Test 7: Duplicate transactions safely deduplicated")

    # -------------------------------------------------------------
    # TEST 8: Missing produce_id Handling
    # -------------------------------------------------------------
    print("\n--- TEST 8: Missing produce_id Handling ---")
    unmatched_tx = pd.DataFrame([
        {"transaction_id": "TX99", "produce_id": "NON_EXISTENT", "quantity_kg": 500, "date": "2026-09-01", "status": "Completed"}
    ])
    unmatched_res = build_transaction_demand_history(unmatched_tx, sample_prod)
    assert unmatched_res.empty, "Transactions with unknown produce_id must be dropped cleanly"
    print("[PASSED] Test 8: Missing produce_id handled cleanly")

    # -------------------------------------------------------------
    # TEST 9: Invalid Quantity Handling
    # -------------------------------------------------------------
    print("\n--- TEST 9: Invalid Quantity Handling ---")
    bad_qty_tx = pd.DataFrame([
        {"transaction_id": "TX1", "produce_id": "P100", "quantity_kg": "invalid", "date": "2026-09-01", "status": "Completed"},
        {"transaction_id": "TX2", "produce_id": "P100", "quantity_kg": -50, "date": "2026-09-01", "status": "Completed"},
        {"transaction_id": "TX3", "produce_id": "P100", "quantity_kg": None, "date": "2026-09-01", "status": "Completed"},
        {"transaction_id": "TX4", "produce_id": "P100", "quantity_kg": 250.0, "date": "2026-09-01", "status": "Completed"},
    ])
    bad_qty_res = build_transaction_demand_history(bad_qty_tx, sample_prod)
    assert len(bad_qty_res) == 1
    assert bad_qty_res.iloc[0]["demand_quantity_kg"] == 250.0
    print("[PASSED] Test 9: Invalid and non-positive quantities safely filtered")

    # -------------------------------------------------------------
    # TEST 10: Invalid Date Handling
    # -------------------------------------------------------------
    print("\n--- TEST 10: Invalid Date Handling ---")
    bad_date_tx = pd.DataFrame([
        {"transaction_id": "TX1", "produce_id": "P100", "quantity_kg": 100, "date": "not-a-date", "status": "Completed"},
        {"transaction_id": "TX2", "produce_id": "P100", "quantity_kg": 200, "date": "2026-09-01", "status": "Completed"},
    ])
    bad_date_res = build_transaction_demand_history(bad_date_tx, sample_prod)
    assert len(bad_date_res) == 1
    assert bad_date_res.iloc[0]["demand_quantity_kg"] == 200.0
    print("[PASSED] Test 10: Unparseable dates safely ignored")

    # -------------------------------------------------------------
    # TEST 11: Nashik + Onion History Generation & Forecasting
    # -------------------------------------------------------------
    print("\n--- TEST 11: Nashik + Onion History Generation & Forecasting ---")
    nashik_onion = derived_df[
        (derived_df["district"] == "Nashik") &
        (derived_df["crop"] == "Onion")
    ].sort_values("date").reset_index(drop=True)
    
    print("Nashik Onion Derived History:")
    print(nashik_onion)
    
    assert len(nashik_onion) == 3, f"Expected exactly 3 historical days for Nashik Onion, got {len(nashik_onion)}"
    assert list(nashik_onion["date"]) == ["2026-09-05", "2026-09-06", "2026-09-07"]
    
    # Run through the demand forecasting module
    fc_nashik_onion = forecast_demand_with_market_context(
        demand_df=derived_df,
        district="Nashik",
        crop="Onion",
        forecast_days=3,
        market_prices_df=prices_df
    )
    assert fc_nashik_onion is not None, "Forecasting should succeed with 3 observations"
    assert fc_nashik_onion["district"] == "Nashik"
    assert fc_nashik_onion["crop"] == "Onion"
    assert fc_nashik_onion["history_days"] == 3
    assert fc_nashik_onion["data_quality"] == "Limited", f"Expected Limited quality for 3 days, got {fc_nashik_onion['data_quality']}"
    assert len(fc_nashik_onion["forecast_values"]) == 3
    print(f"Forecast output for Nashik Onion:")
    for k, v in fc_nashik_onion.items():
        if k != "historical_data":
            print(f"  {k}: {v}")
    print("[PASSED] Test 11: Nashik + Onion derived demand and Limited-quality forecast successful")

    # -------------------------------------------------------------
    # TEST 12: Empty Input Handling
    # -------------------------------------------------------------
    print("\n--- TEST 12: Empty Input Handling ---")
    assert build_transaction_demand_history(None, produce_df).empty
    assert build_transaction_demand_history(transactions_df, None).empty
    assert build_transaction_demand_history(pd.DataFrame(), produce_df).empty
    assert build_transaction_demand_history(transactions_df, pd.DataFrame()).empty
    print("[PASSED] Test 12: Empty inputs return empty DataFrames safely")

    # -------------------------------------------------------------
    # TEST 13: Existing demand.csv Remains Unchanged
    # -------------------------------------------------------------
    print("\n--- TEST 13: Integrity of data/demand.csv ---")
    demand_df_current = load_demand()
    assert len(demand_df_current) == 12, "data/demand.csv should contain exactly 12 rows"
    assert set(demand_df_current["district"].unique()) == {"Pune"}, "data/demand.csv must remain Pune-only without synthetic records"
    print("[PASSED] Test 13: data/demand.csv integrity preserved without modification")

    # -------------------------------------------------------------
    # TEST 14: Farmer Page & Full App Import
    # -------------------------------------------------------------
    print("\n--- TEST 14: Pages and AI Modules Import ---")
    from pages import farmer, buyer, digital_mandi, logistics, consumer
    print("[PASSED] Test 14: Streamlit pages imported cleanly without error")

    print("\n" + "=" * 70)
    print("ALL 14 TRANSACTION DEMAND PREPARATION TESTS PASSED CLEANLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
