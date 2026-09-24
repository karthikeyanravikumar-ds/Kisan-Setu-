"""
Unit test suite for Buyer Intelligence Decision-Support Engine.
Tests:
1. Quantity fill calculation
2. 100% cap on fill percentage
3. Zero requirement quantity handling
4. Price vs Mandi classification (Below, Near, Above)
5. Missing mandi data handling
6. Missing demand forecast handling
7. Normal complete calculation
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

from utils.buyer_intelligence import calculate_buyer_intelligence


def test_quantity_fill_calculation():
    """Test 1: Standard quantity fill percentage calculation."""
    produce_lot = {"quantity_kg": 500.0, "expected_price_per_kg": 30.0}
    buyer_req = {"required_quantity_kg": 600.0, "max_price_per_kg": 35.0}

    res = calculate_buyer_intelligence(produce_lot, buyer_req)
    # 500 / 600 = 83.333% -> 83.3%
    assert res["fill_percentage"] == 83.3
    assert "83.3% quantity coverage" in res["explanation"]


def test_fill_percentage_100_cap():
    """Test 2: Ensure fill percentage is capped at 100.0% when available > required."""
    produce_lot = {"quantity_kg": 1200.0}
    buyer_req = {"required_quantity_kg": 800.0}

    res = calculate_buyer_intelligence(produce_lot, buyer_req)
    assert res["fill_percentage"] == 100.0


def test_zero_requirement():
    """Test 3: Safe handling of zero or negative required quantity."""
    produce_lot = {"quantity_kg": 500.0}
    buyer_req = {"required_quantity_kg": 0.0}

    res = calculate_buyer_intelligence(produce_lot, buyer_req)
    assert res["fill_percentage"] == 0.0

    # Negative required quantity
    buyer_req_neg = {"required_quantity_kg": -100.0}
    res_neg = calculate_buyer_intelligence(produce_lot, buyer_req_neg)
    assert res_neg["fill_percentage"] == 0.0


def test_price_vs_mandi_classification():
    """Test 4: Verify 'Below mandi benchmark', 'Near mandi benchmark', 'Above mandi benchmark'."""
    buyer_req = {"required_quantity_kg": 500.0}
    mandi = {"modal_price_per_kg": 30.00}

    # Case A: Above mandi benchmark (> +0.50)
    lot_above = {"expected_price_per_kg": 32.50}
    res_above = calculate_buyer_intelligence(lot_above, buyer_req, mandi_benchmark=mandi)
    assert res_above["price_difference_vs_mandi"] == 2.50
    assert res_above["market_context"] == "Above mandi benchmark"

    # Case B: Near mandi benchmark (within +/- 0.50)
    lot_near = {"expected_price_per_kg": 30.20}
    res_near = calculate_buyer_intelligence(lot_near, buyer_req, mandi_benchmark=mandi)
    assert res_near["price_difference_vs_mandi"] == 0.20
    assert res_near["market_context"] == "Near mandi benchmark"

    # Case C: Below mandi benchmark (< -0.50)
    lot_below = {"expected_price_per_kg": 27.50}
    res_below = calculate_buyer_intelligence(lot_below, buyer_req, mandi_benchmark=mandi)
    assert res_below["price_difference_vs_mandi"] == -2.50
    assert res_below["market_context"] == "Below mandi benchmark"


def test_missing_mandi():
    """Test 5: Safe handling of missing mandi benchmark data."""
    produce_lot = {"expected_price_per_kg": 30.0, "quantity_kg": 500.0}
    buyer_req = {"required_quantity_kg": 500.0}

    res = calculate_buyer_intelligence(produce_lot, buyer_req, mandi_benchmark=None)
    assert res["mandi_modal_price_per_kg"] is None
    assert res["price_difference_vs_mandi"] is None
    assert res["market_context"] == "Mandi benchmark unavailable"


def test_missing_demand():
    """Test 6: Safe handling of missing demand forecast."""
    produce_lot = {"crop": "Onion", "quantity_kg": 500.0}
    buyer_req = {"required_quantity_kg": 500.0}

    res = calculate_buyer_intelligence(produce_lot, buyer_req, demand_forecast=None)
    assert res["demand_signal"] == "Unavailable"
    assert res["demand_source"] == "Unavailable"
    assert res["demand_percentage_change"] is None


def test_normal_calculation():
    """Test 7: Full normal calculation with all intelligence layers populated."""
    produce_lot = {
        "produce_id": "P001",
        "farmer_id": "F001",
        "farmer_name": "Ramesh Patil",
        "crop": "Onion",
        "district": "Nashik",
        "location": "Niphad",
        "quantity_kg": 500.0,
        "quality_grade": "A",
        "expected_price_per_kg": 31.0,
        "distance_km": 145.0,
        "match_score": 94,
    }
    buyer_req = {
        "buyer_id": "B001",
        "name": "Pune Fresh Retail",
        "district": "Pune",
        "location": "Pune",
        "required_quantity_kg": 600.0,
        "max_price_per_kg": 38.0,
        "min_quality": "A",
    }
    mandi_benchmark = {
        "modal_price_per_kg": 28.40,
        "market": "Pune APMC",
        "is_live": True,
    }
    demand_forecast = {
        "trend": "Increasing",
        "percentage_change": 12.5,
        "demand_source": "Platform transaction history",
    }
    logistics = {
        "cost_per_km": 4.5,
        "base_cost": 300.0,
    }

    res = calculate_buyer_intelligence(
        produce_lot=produce_lot,
        buyer_requirement=buyer_req,
        mandi_benchmark=mandi_benchmark,
        demand_forecast=demand_forecast,
        logistics=logistics,
    )

    assert res["produce_id"] == "P001"
    assert res["farmer_name"] == "Ramesh Patil"
    assert res["crop"] == "Onion"
    assert res["available_quantity_kg"] == 500.0
    assert res["buyer_required_quantity_kg"] == 600.0
    assert res["fill_percentage"] == 83.3
    assert res["quality_grade"] == "A"
    assert res["farmer_expected_price_per_kg"] == 31.0
    assert res["mandi_modal_price_per_kg"] == 28.40
    assert res["price_difference_vs_mandi"] == 2.60
    assert res["market_context"] == "Above mandi benchmark"
    assert res["demand_signal"] == "Increasing"
    assert res["demand_percentage_change"] == 12.5
    assert res["distance_km"] == 145.0
    assert res["logistics_cost"] == 952.5 # 300 + 145 * 4.5
    assert res["match_score"] == 94
    assert "This lot provides 500 kg against a requirement of 600 kg" in res["explanation"]
    assert "₹31.00/kg compared with the live mandi modal benchmark of ₹28.40/kg" in res["explanation"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
