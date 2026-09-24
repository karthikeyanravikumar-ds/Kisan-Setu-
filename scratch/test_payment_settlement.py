"""
Unit test suite for Payment & Settlement Simulation Engine.
Tests:
1. Gross calculation & settlement breakdown
2. Logistics deduction & platform fee handling
3. Net settlement amount calculation
4. Zero & negative value guards
5. Missing transaction lookup
6. Payment status lifecycle transitions
7. Settlement status lifecycle transitions
8. Preservation of separate Estimated Net Realization vs Actual Settlement concepts
"""

import sys
import os
import pytest
import pandas as pd
import tempfile

# Add repository root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from utils.payment_settlement import (
    calculate_settlement_breakdown,
    get_payment_for_transaction,
    record_or_update_payment,
    update_payment_status,
    update_settlement_status,
    load_payments,
    VALID_PAYMENT_STATUSES,
    VALID_SETTLEMENT_STATUSES,
    DISCLAIMER_TEXT,
)


def test_settlement_breakdown_and_gross():
    """Test 1: Gross transaction value calculation and breakdown."""
    # 500 kg @ ₹30/kg = ₹15,000 gross
    gross = 500.0 * 30.0
    res = calculate_settlement_breakdown(gross_amount=gross)

    assert res["gross_amount"] == 15000.0
    assert res["logistics_cost"] == 0.0
    assert res["platform_fee"] == 0.0
    assert res["net_settlement"] == 15000.0
    assert res["disclaimer"] == DISCLAIMER_TEXT


def test_logistics_deduction_and_platform_fee():
    """Test 2: Logistics freight deduction and optional platform fee calculation."""
    # Gross: ₹16,000, Logistics: ₹3,500, Platform Fee: ₹250
    res = calculate_settlement_breakdown(
        gross_amount=16000.0,
        logistics_cost=3500.0,
        platform_fee=250.0,
    )

    assert res["gross_amount"] == 16000.0
    assert res["logistics_cost"] == 3500.0
    assert res["platform_fee"] == 250.0
    # Net settlement = 16000 - 3500 - 250 = 12250.0
    assert res["net_settlement"] == 12250.0


def test_zero_and_edge_values():
    """Test 3: Zero values and invalid input handling."""
    res_zero = calculate_settlement_breakdown(gross_amount=0.0, logistics_cost=0.0, platform_fee=0.0)
    assert res_zero["gross_amount"] == 0.0
    assert res_zero["net_settlement"] == 0.0

    # Negative / None inputs guarded to 0.0
    res_invalid = calculate_settlement_breakdown(gross_amount=-100.0, logistics_cost=None, platform_fee="abc")
    assert res_invalid["gross_amount"] == 0.0
    assert res_invalid["logistics_cost"] == 0.0
    assert res_invalid["platform_fee"] == 0.0
    assert res_invalid["net_settlement"] == 0.0


def test_missing_transaction():
    """Test 4: Missing or invalid transaction lookup returns None."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
        temp_path = tf.name

    try:
        # Empty file lookup
        res = get_payment_for_transaction("TX_DOES_NOT_EXIST", file_path=temp_path)
        assert res is None

        # None / empty ID
        assert get_payment_for_transaction("", file_path=temp_path) is None
        assert get_payment_for_transaction(None, file_path=temp_path) is None
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_payment_and_settlement_persistence():
    """Test 5: Create and retrieve payment record in CSV."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
        temp_path = tf.name

    try:
        rec = record_or_update_payment(
            transaction_id="TX_TEST_01",
            buyer_id="B001",
            farmer_id="F001",
            gross_amount=12000.0,
            logistics_cost=2000.0,
            platform_fee=100.0,
            payment_status="Payment Pending",
            settlement_status="Settlement Pending",
            file_path=temp_path,
        )

        assert rec["transaction_id"] == "TX_TEST_01"
        assert rec["gross_amount"] == 12000.0
        assert rec["logistics_cost"] == 2000.0
        assert rec["platform_fee"] == 100.0
        assert rec["net_settlement"] == 9900.0
        assert rec["payment_status"] == "Payment Pending"
        assert rec["settlement_status"] == "Settlement Pending"

        # Lookup
        lookup = get_payment_for_transaction("TX_TEST_01", file_path=temp_path)
        assert lookup is not None
        assert lookup["net_settlement"] == 9900.0
        assert lookup["disclaimer"] == DISCLAIMER_TEXT
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_payment_status_transitions():
    """Test 6: Lifecycle state transitions for Payment Status."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
        temp_path = tf.name

    try:
        # Create initial record
        record_or_update_payment(
            transaction_id="TX_PAY_FLOW",
            buyer_id="B002",
            farmer_id="F002",
            gross_amount=10000.0,
            logistics_cost=1000.0,
            payment_status="Payment Pending",
            file_path=temp_path,
        )

        # 1. Transition: Payment Pending -> Payment Received
        up1 = update_payment_status("TX_PAY_FLOW", "Payment Received", payment_date="2026-09-08", file_path=temp_path)
        assert up1["payment_status"] == "Payment Received"
        assert up1["payment_date"] == "2026-09-08"

        # 2. Transition: Payment Received -> Refunded
        up2 = update_payment_status("TX_PAY_FLOW", "Refunded", file_path=temp_path)
        assert up2["payment_status"] == "Refunded"

        # 3. Invalid status rejected
        assert update_payment_status("TX_PAY_FLOW", "InvalidPaymentStatus", file_path=temp_path) is None

        # 4. Non-existent transaction rejected
        assert update_payment_status("TX_NONEXISTENT", "Payment Received", file_path=temp_path) is None
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_settlement_status_transitions():
    """Test 7: Lifecycle state transitions for Settlement Status."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
        temp_path = tf.name

    try:
        # Create initial record
        record_or_update_payment(
            transaction_id="TX_SETTLE_FLOW",
            buyer_id="B003",
            farmer_id="F003",
            gross_amount=8000.0,
            logistics_cost=800.0,
            settlement_status="Settlement Pending",
            file_path=temp_path,
        )

        # 1. Transition: Settlement Pending -> Settled
        up1 = update_settlement_status("TX_SETTLE_FLOW", "Settled", settlement_date="2026-09-09", file_path=temp_path)
        assert up1["settlement_status"] == "Settled"
        assert up1["settlement_date"] == "2026-09-09"

        # 2. Transition: Settled -> Cancelled
        up2 = update_settlement_status("TX_SETTLE_FLOW", "Cancelled", file_path=temp_path)
        assert up2["settlement_status"] == "Cancelled"

        # 3. Invalid status rejected
        assert update_settlement_status("TX_SETTLE_FLOW", "InvalidSettlementStatus", file_path=temp_path) is None
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_separate_estimated_vs_actual_settlement():
    """Test 8: Ensure Estimated Net Realization concept is distinct and not mutated by settlement."""
    estimated_farmer_realization = 14500.0 # From pre-trade intelligence estimation
    actual_gross = 15000.0
    actual_logistics = 1800.0
    actual_fee = 150.0

    settlement = calculate_settlement_breakdown(
        gross_amount=actual_gross,
        logistics_cost=actual_logistics,
        platform_fee=actual_fee,
    )

    # Actual settlement differs from estimated pre-trade realization
    assert settlement["net_settlement"] == 13050.0
    assert settlement["net_settlement"] != estimated_farmer_realization
    assert estimated_farmer_realization == 14500.0 # Estimated value unmutated


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
