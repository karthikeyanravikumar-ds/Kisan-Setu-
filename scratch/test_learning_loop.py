"""
Unit test suite for the Feedback -> Learning Loop & Performance Analytics.
Tests:
1. Empty feedback DataFrame handling
2. Missing required columns handling
3. Normal feedback evaluation
4. Transaction completion & acceptance rate calculations
5. Mandi benchmark realization comparison
6. Insufficient data handling & default states
7. Governance constraints (retraining prevention & policy notes)
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np

# Add repository root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from utils.learning_loop import (
    calculate_match_acceptance,
    calculate_transaction_completion,
    calculate_feedback_summary,
    calculate_market_realization_comparison,
    calculate_forecast_performance,
    calculate_quality_feedback_summary,
    calculate_learning_summary,
    LEARNING_NOTE,
    NO_RETRAIN_NOTE,
)


def test_empty_feedback():
    """Test 1: Empty feedback dataframe handling."""
    empty_df = pd.DataFrame()
    res = calculate_feedback_summary(empty_df)

    assert res["total_feedback_count"] == 0
    assert res["farmer"]["count"] == 0
    assert res["farmer"]["avg_rating"] is None
    assert res["farmer"]["display_rating"] == "Insufficient data"
    assert res["farmer"]["comments"] == []
    assert res["buyer"]["count"] == 0
    assert res["buyer"]["avg_rating"] is None
    assert res["buyer"]["display_rating"] == "Insufficient data"
    assert res["buyer"]["comments"] == []
    assert res["all_feedback"] == []


def test_missing_columns():
    """Test 2: Missing columns in feedback and transaction dataframes."""
    bad_feedback_df = pd.DataFrame([{"wrong_col_1": 123, "wrong_col_2": "text"}])
    res_fb = calculate_feedback_summary(bad_feedback_df)
    assert res_fb["total_feedback_count"] == 0
    assert res_fb["farmer"]["display_rating"] == "Insufficient data"

    bad_tx_df = pd.DataFrame([{"random_id": "T001", "foo": "bar"}])
    res_match = calculate_match_acceptance(bad_tx_df)
    assert res_match["acceptance_rate_pct"] is None
    assert res_match["display_text"] == "Insufficient data"

    res_comp = calculate_transaction_completion(bad_tx_df)
    assert res_comp["completion_rate_pct"] is None
    assert res_comp["display_text"] == "Insufficient data"


def test_normal_feedback():
    """Test 3: Normal feedback calculation across farmers and buyers."""
    feedback_df = pd.DataFrame([
        {"feedback_id": "FB001", "user_type": "Farmer", "user_id": "F001", "transaction_id": "T001", "rating": 5, "comment": "Great fair price"},
        {"feedback_id": "FB002", "user_type": "Farmer", "user_id": "F002", "transaction_id": "T002", "rating": 4, "comment": "Good dispatch speed"},
        {"feedback_id": "FB003", "user_type": "Buyer", "user_id": "B001", "transaction_id": "T001", "rating": 4, "comment": "High quality produce"},
    ])

    res = calculate_feedback_summary(feedback_df)
    assert res["total_feedback_count"] == 3
    assert res["farmer"]["count"] == 2
    assert res["farmer"]["avg_rating"] == 4.5
    assert res["farmer"]["display_rating"] == "4.5 / 5.0"
    assert len(res["farmer"]["comments"]) == 2

    assert res["buyer"]["count"] == 1
    assert res["buyer"]["avg_rating"] == 4.0
    assert res["buyer"]["display_rating"] == "4.0 / 5.0"
    assert len(res["buyer"]["comments"]) == 1


def test_transaction_completion_and_acceptance():
    """Test 4: Match acceptance and completion rates from transactions."""
    tx_df = pd.DataFrame([
        {"transaction_id": "T01", "status": "Completed"},
        {"transaction_id": "T02", "status": "Delivered"},
        {"transaction_id": "T03", "status": "In Transit"},
        {"transaction_id": "T04", "status": "Confirmed"},
        {"transaction_id": "T05", "status": "Order Placed"},
        {"transaction_id": "T06", "status": "Cancelled"},
    ])

    # Acceptance: Completed, Delivered, In Transit, Confirmed (4 out of 6)
    acc = calculate_match_acceptance(tx_df)
    assert acc["total_matches"] == 6
    assert acc["accepted_matches"] == 4
    assert acc["rejected_matches"] == 1
    assert acc["pending_matches"] == 1
    assert acc["acceptance_rate_pct"] == round((4 / 6) * 100.0, 1) # 66.7%
    assert acc["display_text"] == "66.7%"

    # Completion: Completed, Delivered (2 out of 6)
    comp = calculate_transaction_completion(tx_df)
    assert comp["total_transactions"] == 6
    assert comp["completed_transactions"] == 2
    assert comp["completion_rate_pct"] == round((2 / 6) * 100.0, 1) # 33.3%
    assert comp["display_text"] == "33.3%"


def test_benchmark_comparison():
    """Test 5: Market realization comparison against mandi benchmarks."""
    tx_df = pd.DataFrame([
        {"transaction_id": "T1", "produce_id": "P1", "price_per_kg": 32.0},
        {"transaction_id": "T2", "produce_id": "P2", "price_per_kg": 34.0},
    ])
    pr_df = pd.DataFrame([
        {"produce_id": "P1", "crop": "Onion", "district": "Nashik"},
        {"produce_id": "P2", "crop": "Tomato", "district": "Nashik"},
    ])
    mk_df = pd.DataFrame([
        {"crop": "Onion", "modal_price_per_kg": 28.0},
        {"crop": "Tomato", "modal_price_per_kg": 30.0},
    ])

    res = calculate_market_realization_comparison(tx_df, pr_df, mk_df)
    assert res["transactions_compared"] == 2
    assert res["avg_realized_price"] == 33.0 # (32 + 34) / 2
    assert res["avg_mandi_benchmark"] == 29.0 # (28 + 30) / 2
    assert res["avg_premium_per_kg"] == 4.0 # 33.0 - 29.0
    assert res["avg_premium_pct"] == round((4.0 / 29.0) * 100.0, 1) # 13.8%
    assert "+₹4.00/kg" in res["display_text"]


def test_insufficient_data():
    """Test 6: Graceful handling of empty or None datasets with 'Insufficient data'."""
    res_real = calculate_market_realization_comparison(pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
    assert res_real["display_text"] == "Insufficient data"
    assert res_real["avg_realized_price"] is None

    res_summary = calculate_learning_summary(
        transactions_df=pd.DataFrame(),
        feedback_df=pd.DataFrame(),
        produce_df=pd.DataFrame(),
        prices_df=pd.DataFrame(),
        demand_df=pd.DataFrame(),
    )
    assert res_summary["status"] == "insufficient_data"
    assert res_summary["transactions_analyzed"] == 0
    assert res_summary["feedback_received"] == 0
    assert res_summary["match_acceptance"]["display_text"] == "Insufficient data"
    assert res_summary["completion_rate"]["display_text"] == "Insufficient data"
    assert res_summary["market_realization"]["display_text"] == "Insufficient data"
    assert res_summary["forecast_performance"]["display_text"] == "Insufficient data"


def test_governance_and_policies():
    """Test 7: Governance compliance (no retrain claim and mandatory learning note)."""
    summary = calculate_learning_summary()
    assert summary["learning_note"] == LEARNING_NOTE
    assert "retrained" not in summary["model_retraining_governance"].lower()
    assert "Feedback is captured for future model evaluation and improvement." in summary["learning_note"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
