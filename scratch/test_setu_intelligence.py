"""
Test suite for Setu Intelligence Decision-Support Engine.
"""
import sys
import os
import pytest
import pandas as pd

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.setu_intelligence import calculate_setu_intelligence


def test_normal_calculation():
    """Test 1: Normal calculation with full inputs."""
    produce_lot = {
        "crop": "Onion",
        "district": "Nashik",
        "quantity_kg": 500.0,
        "expected_price_per_kg": 30.0,
    }
    mandi_benchmark = {
        "modal_price_per_kg": 28.40,
        "min_price_per_kg": 25.0,
        "max_price_per_kg": 32.0,
        "market": "APMC Pimpalgaon",
        "is_live": True,
    }
    buyer_match = {
        "buyer_id": "B001",
        "buyer_name": "Pune Fresh Retail",
        "buyer_type": "Retailer",
        "max_price_per_kg": 31.0,
        "match_score": 94,
        "required_quantity_kg": 600.0,
        "distance_km": 145.0,
    }
    demand_forecast = {
        "trend": "Increasing",
        "percentage_change": 10.4,
        "forecast_demand_kg": 4748.0,
        "demand_source": "Historical demand dataset",
        "data_quality": "Moderate",
        "history_days": 6,
    }
    logistics = {
        "cost_per_km": 4.5,
        "base_cost": 300.0,
    }

    res = calculate_setu_intelligence(
        produce_lot=produce_lot,
        mandi_benchmark=mandi_benchmark,
        buyer_match=buyer_match,
        demand_forecast=demand_forecast,
        logistics=logistics,
    )

    assert res["buyer_gross_value"] == 15500.0 # 500 * 31.0
    assert res["logistics_cost"] == 952.5 # 300 + 145 * 4.5
    assert res["estimated_net_realization"] == 14547.5 # 15500 - 952.5
    assert res["effective_net_per_kg"] == 29.09 # 14547.5 / 500 = 29.095 -> 29.09
    assert res["mandi_modal_price_per_kg"] == 28.40
    assert res["mandi_benchmark_gross_value"] == 14200.0 # 500 * 28.40
    assert res["mandi_net_realization"] == 13247.5 # 14200 - 952.5
    assert res["price_spread_per_kg"] == 2.60 # 31.0 - 28.40
    assert res["net_difference"] == 1300.0 # 14547.5 - 13247.5 = 1300.0 (500 * 2.60)
    assert res["demand_signal"] == "Increasing"
    assert "decision_factors" in res
    assert "price_vs_mandi" in res["decision_factors"]
    assert "demand_outlook" in res["decision_factors"]
    assert "logistics_impact" in res["decision_factors"]
    assert "explanation" in res
    assert "Buyer offer is ₹31.00/kg" in res["explanation"]


def test_missing_buyer_offer():
    """Test 2: Missing buyer offer handling."""
    produce_lot = {"crop": "Onion", "district": "Nashik", "quantity_kg": 500.0}
    mandi_benchmark = {"modal_price_per_kg": 28.40}

    res = calculate_setu_intelligence(
        produce_lot=produce_lot,
        mandi_benchmark=mandi_benchmark,
        buyer_match=None,
    )

    assert res["buyer_offer_price_per_kg"] is None
    assert res["buyer_gross_value"] == 0.0
    assert res["estimated_net_realization"] == 0.0
    assert res["effective_net_per_kg"] == 0.0
    assert res["mandi_benchmark_gross_value"] == 14200.0
    assert res["price_spread_per_kg"] is None
    assert "explanation" in res


def test_missing_mandi_data():
    """Test 3: Missing mandi data handling."""
    produce_lot = {"crop": "Tomato", "district": "Pune", "quantity_kg": 300.0}
    buyer_match = {"buyer_name": "Metro Cash", "max_price_per_kg": 35.0, "distance_km": 50.0}

    res = calculate_setu_intelligence(
        produce_lot=produce_lot,
        mandi_benchmark=None,
        buyer_match=buyer_match,
    )

    assert res["mandi_modal_price_per_kg"] is None
    assert res["mandi_benchmark_gross_value"] is None
    assert res["buyer_gross_value"] == 10500.0
    assert res["price_spread_per_kg"] is None
    assert res["net_difference"] is None


def test_zero_quantity():
    """Test 4: Zero quantity produce lot."""
    produce_lot = {"crop": "Wheat", "district": "Nashik", "quantity_kg": 0.0}
    buyer_match = {"max_price_per_kg": 30.0, "distance_km": 100.0}
    mandi_benchmark = {"modal_price_per_kg": 28.0}

    res = calculate_setu_intelligence(
        produce_lot=produce_lot,
        mandi_benchmark=mandi_benchmark,
        buyer_match=buyer_match,
    )

    assert res["quantity_kg"] == 0.0
    assert res["buyer_gross_value"] == 0.0
    assert res["estimated_net_realization"] == 0.0
    assert res["effective_net_per_kg"] == 0.0


def test_logistics_cost():
    """Test 5: Logistics cost calculation and custom override."""
    produce_lot = {"crop": "Onion", "quantity_kg": 1000.0}
    buyer_match = {"max_price_per_kg": 30.0, "distance_km": 200.0}
    logistics = {"cost_per_km": 5.0, "base_cost": 500.0}

    # Standard formula: 500 + 200 * 5 = 1500
    res1 = calculate_setu_intelligence(produce_lot, buyer_match=buyer_match, logistics=logistics)
    assert res1["logistics_cost"] == 1500.0

    # Custom override
    res2 = calculate_setu_intelligence(produce_lot, buyer_match=buyer_match, custom_logistics_cost=850.0)
    assert res2["logistics_cost"] == 850.0


def test_demand_signal():
    """Test 6: Demand signal parsing and fallbacks."""
    produce_lot = {"crop": "Onion", "quantity_kg": 500.0}

    # Case A: Increasing
    res_inc = calculate_setu_intelligence(produce_lot, demand_forecast={"trend": "Increasing", "percentage_change": 15.0})
    assert res_inc["demand_signal"] == "Increasing"

    # Case B: Stable
    res_stb = calculate_setu_intelligence(produce_lot, demand_forecast={"trend": "Stable", "percentage_change": 0.5})
    assert res_stb["demand_signal"] == "Stable"

    # Case C: Decreasing
    res_dec = calculate_setu_intelligence(produce_lot, demand_forecast={"trend": "Decreasing", "percentage_change": -12.0})
    assert res_dec["demand_signal"] == "Decreasing"

    # Case D: None / Invalid
    res_unav = calculate_setu_intelligence(produce_lot, demand_forecast=None)
    assert res_unav["demand_signal"] == "Unavailable"


def test_net_realization_calculation():
    """Test 7: Net realization calculation accuracy."""
    produce_lot = {"crop": "Onion", "quantity_kg": 800.0}
    buyer_match = {"max_price_per_kg": 32.50, "distance_km": 100.0}
    logistics = {"cost_per_km": 4.0, "base_cost": 200.0} # 200 + 400 = 600

    res = calculate_setu_intelligence(produce_lot, buyer_match=buyer_match, logistics=logistics)
    gross = 800.0 * 32.50 # 26,000
    freight = 600.0
    net = gross - freight # 25,400

    assert res["buyer_gross_value"] == gross
    assert res["logistics_cost"] == freight
    assert res["estimated_net_realization"] == net
    assert res["effective_net_per_kg"] == round(net / 800.0, 2) # 31.75


def test_true_net_to_net_difference():
    """Test 8: Verify true net-to-net comparison and mandi_net_realization."""
    produce_lot = {"crop": "Tomato", "quantity_kg": 1000.0}
    buyer_match = {"max_price_per_kg": 40.0, "distance_km": 100.0}
    mandi_benchmark = {"modal_price_per_kg": 35.0}
    logistics = {"cost_per_km": 5.0, "base_cost": 500.0} # 500 + 500 = 1000.0

    res = calculate_setu_intelligence(
        produce_lot=produce_lot,
        buyer_match=buyer_match,
        mandi_benchmark=mandi_benchmark,
        logistics=logistics,
    )

    buyer_net = 1000.0 * 40.0 - 1000.0 # 39,000.0
    mandi_gross = 1000.0 * 35.0 # 35,000.0
    mandi_net = mandi_gross - 1000.0 # 34,000.0
    net_diff = buyer_net - mandi_net # 5,000.0

    assert res["buyer_gross_value"] == 40000.0
    assert res["logistics_cost"] == 1000.0
    assert res["estimated_net_realization"] == buyer_net
    assert res["mandi_benchmark_gross_value"] == mandi_gross
    assert res["mandi_net_realization"] == mandi_net
    assert res["net_difference"] == net_diff
    assert res["price_spread_per_kg"] == 5.0


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))


