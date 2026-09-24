"""
Unit test suite for Demand Forecast Evaluation Engine.
Tests:
1. Metric calculations (MAE, RMSE, MAPE)
2. Chronological split (strict time-ordering, no random shuffle)
3. Insufficient history handling
4. Zero actual values handling for MAPE
5. Nashik transaction-derived demand evaluation
"""

import sys
import os
import pytest
import numpy as np
import pandas as pd

# Add repository root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scratch.evaluate_demand_forecast import (
    calculate_metrics,
    evaluate_demand_series,
    run_full_evaluation,
)
from utils.data_loader import load_demand, load_transactions, load_produce
from utils.demand_data import build_transaction_demand_history


def test_metric_calculations():
    """Test 1: Verify MAE, RMSE, and MAPE calculations with known values."""
    actuals = [100.0, 200.0, 300.0, 400.0]
    predictions = [110.0, 190.0, 315.0, 380.0]
    # Errors: [-10, 10, -15, 20]
    # Abs errors: [10, 10, 15, 20] -> MAE = 55 / 4 = 13.75
    # Squared errors: [100, 100, 225, 400] = 825 -> RMSE = sqrt(825/4) = sqrt(206.25) = 14.3614 -> 14.36
    # Rel errors: [10/100, 10/200, 15/300, 20/400] = [0.10, 0.05, 0.05, 0.05] -> MAPE = 25% / 4 = 6.25%

    res = calculate_metrics(actuals, predictions)

    assert res["mae"] == 13.75
    assert res["rmse"] == 14.36
    assert res["mape"] == 6.25


def test_chronological_split():
    """Test 2: Verify strict chronological splitting without shuffling or leakage."""
    dates = pd.date_range("2026-09-01", periods=6, freq="D")
    df = pd.DataFrame({
        "date": dates,
        "district": ["Pune"] * 6,
        "crop": ["Onion"] * 6,
        "demand_quantity_kg": [1000, 1100, 1200, 1300, 1400, 1500],
        "orders": [10, 11, 12, 13, 14, 15],
    })

    # Test with test_size = 2
    res = evaluate_demand_series(df, "Pune", "Onion", test_size=2)

    assert res["status"] == "success"
    assert res["n_total"] == 6
    assert res["n_train"] == 4
    assert res["n_test"] == 2
    assert res["train_dates"] == ("2026-09-01", "2026-09-04")
    assert res["test_dates"] == ("2026-09-05", "2026-09-06")
    assert res["actuals"] == [1400, 1500]
    assert len(res["predictions"]) == 2
    # Linear trend is perfectly y = 1000 + 100 * day_index. Predictions for day 4 and 5 should be 1400 and 1500.
    assert res["predictions"] == [1400.0, 1500.0]
    assert res["mae"] == 0.0
    assert res["rmse"] == 0.0
    assert res["mape"] == 0.0


def test_insufficient_history():
    """Test 3: Insufficient history handling when observations < 4."""
    # Only 2 observations (cannot train model with min 3)
    df_2 = pd.DataFrame({
        "date": ["2026-09-01", "2026-09-02"],
        "district": ["Pune", "Pune"],
        "crop": ["Potato", "Potato"],
        "demand_quantity_kg": [500, 600],
    })

    res_2 = evaluate_demand_series(df_2, "Pune", "Potato")
    assert res_2["status"] == "insufficient_history"
    assert res_2["n_total"] == 2
    assert res_2["n_train"] == 0
    assert res_2["n_test"] == 0
    assert res_2["mae"] is None

    # Exactly 3 observations (can train, but cannot perform out-of-sample test split)
    df_3 = pd.DataFrame({
        "date": ["2026-09-01", "2026-09-02", "2026-09-03"],
        "district": ["Pune", "Pune", "Pune"],
        "crop": ["Potato", "Potato", "Potato"],
        "demand_quantity_kg": [500, 600, 700],
    })

    res_3 = evaluate_demand_series(df_3, "Pune", "Potato")
    assert res_3["status"] == "insufficient_history"
    assert res_3["n_total"] == 3
    assert res_3["n_train"] == 3
    assert res_3["n_test"] == 0
    assert res_3["mae"] is None
    assert "Sample size too small" in res_3["sample_note"]


def test_zero_actual_values_mape():
    """Test 4: Safe handling of zero actual values for MAPE calculation."""
    # Case A: Actuals containing zeros
    actuals = [0.0, 100.0, 200.0]
    predictions = [10.0, 110.0, 210.0]

    res = calculate_metrics(actuals, predictions)
    assert res["mae"] == 10.0
    assert res["rmse"] == 10.0
    # MAPE calculated only over non-zero actuals: (10/100 + 10/200)/2 = 0.075 -> 7.5%
    assert res["mape"] == 7.5

    # Case B: All zeros in actuals
    all_zeros_actuals = [0.0, 0.0, 0.0]
    res_zero = calculate_metrics(all_zeros_actuals, predictions)
    assert res_zero["mae"] == 110.0
    assert res_zero["mape"] is None # Handled cleanly without ZeroDivisionError


def test_nashik_transaction_derived_data():
    """Test 5: Evaluation on Nashik transaction-derived demand series."""
    tx_df = load_transactions()
    prod_df = load_produce()
    tx_demand_df = build_transaction_demand_history(tx_df, prod_df)

    res = evaluate_demand_series(
        demand_df=tx_demand_df,
        district="Nashik",
        crop="Onion",
        source_label="Platform transaction-derived demand activity",
        test_size=1,
    )

    # Nashik + Onion in current dataset has 3 observations (2026-09-05, 2026-09-06, 2026-09-07)
    assert res["dataset_source"] == "Platform transaction-derived demand activity"
    assert res["n_total"] == 3
    assert res["status"] == "insufficient_history"
    assert res["n_test"] == 0
    assert res["mae"] is None
    assert "Sample has 3 observation(s)" in res["message"]


def test_run_full_evaluation_execution():
    """Test 6: Integration execution of run_full_evaluation."""
    results = run_full_evaluation()
    assert isinstance(results, list)
    assert len(results) == 3

    # Check Pune Onion
    pune_onion = next(r for r in results if r["district"] == "Pune" and r["crop"] == "Onion")
    assert pune_onion["status"] == "success"
    assert pune_onion["n_total"] == 6
    assert pune_onion["n_train"] == 4
    assert pune_onion["n_test"] == 2
    assert pune_onion["mae"] == 65.0
    assert pune_onion["rmse"] == 66.71
    assert pune_onion["mape"] == 1.54

    # Check Pune Tomato
    pune_tomato = next(r for r in results if r["district"] == "Pune" and r["crop"] == "Tomato")
    assert pune_tomato["status"] == "success"
    assert pune_tomato["n_total"] == 6
    assert pune_tomato["n_train"] == 4
    assert pune_tomato["n_test"] == 2
    assert pune_tomato["mae"] == 25.0
    assert pune_tomato["rmse"] == 35.36
    assert pune_tomato["mape"] == 0.96


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
