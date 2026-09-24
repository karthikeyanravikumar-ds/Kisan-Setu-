"""
Unit test suite for Logistics Partner Management & Prototype Orchestration.
Tests:
1. Capacity matching
2. Insufficient capacity handling
3. Unavailable partner exclusion
4. Service area / coverage validation
5. Freight calculation accuracy
6. Partner assignment to transaction
7. Status transitions lifecycle
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

from logistics.partner_manager import (
    load_logistics_partners,
    match_logistics_partners,
    assign_partner_to_transaction,
    update_partner_assignment_status,
    get_partner_for_transaction,
    load_partner_assignments,
    VALID_PARTNER_STATUSES,
)


@pytest.fixture
def mock_partners_df():
    """Provides a controlled mock partners DataFrame."""
    return pd.DataFrame([
        {
            "partner_id": "LP001",
            "partner_name": "Sahyadri Agro Transporters",
            "vehicle_type": "Mini Truck",
            "capacity_kg": 1200.0,
            "base_location": "Nashik",
            "service_regions": "Nashik, Pune, Ahmednagar, Mumbai",
            "cost_per_km": 28.0,
            "base_cost": 500.0,
            "availability": "Available",
            "rating": 4.8,
            "contact_phone": "+91 98220 44101",
        },
        {
            "partner_id": "LP002",
            "partner_name": "Godavari Express Logistics",
            "vehicle_type": "Medium Eicher",
            "capacity_kg": 2500.0,
            "base_location": "Nashik",
            "service_regions": "Nashik, Pune, Mumbai",
            "cost_per_km": 35.0,
            "base_cost": 800.0,
            "availability": "Available",
            "rating": 4.7,
            "contact_phone": "+91 98220 44102",
        },
        {
            "partner_id": "LP003",
            "partner_name": "Deccan Rural Haulage",
            "vehicle_type": "Pickup 4x4",
            "capacity_kg": 600.0,
            "base_location": "Ahmednagar",
            "service_regions": "Ahmednagar, Pune",
            "cost_per_km": 22.0,
            "base_cost": 350.0,
            "availability": "Available",
            "rating": 4.9,
            "contact_phone": "+91 98220 44103",
        },
        {
            "partner_id": "LP004",
            "partner_name": "Kisan Setu Fleet Unit 1",
            "vehicle_type": "Refrigerated Van",
            "capacity_kg": 1500.0,
            "base_location": "Pune",
            "service_regions": "Pune, Mumbai, Nashik",
            "cost_per_km": 38.0,
            "base_cost": 900.0,
            "availability": "Busy", # Unavailable
            "rating": 4.6,
            "contact_phone": "+91 98220 44104",
        },
    ])


def test_capacity_matching(mock_partners_df):
    """Test 1: Matches partners with capacity >= required load."""
    matches = match_logistics_partners(
        required_quantity_kg=500.0,
        origin="Niphad, Nashik",
        destination="Pune",
        partners_df=mock_partners_df,
    )

    # 500 kg can be carried by LP001 (1200kg), LP002 (2500kg), LP003 (600kg). LP004 is Busy.
    p_ids = [m["partner_id"] for m in matches]
    assert "LP001" in p_ids
    assert "LP002" in p_ids
    assert "LP004" not in p_ids # Busy partner excluded


def test_insufficient_capacity(mock_partners_df):
    """Test 2: Excludes partners when required load exceeds their vehicle capacity."""
    # 2000 kg load: LP001 (1200kg) and LP003 (600kg) should be excluded
    matches = match_logistics_partners(
        required_quantity_kg=2000.0,
        origin="Nashik",
        destination="Pune",
        partners_df=mock_partners_df,
    )

    p_ids = [m["partner_id"] for m in matches]
    assert "LP002" in p_ids # 2500 kg capacity
    assert "LP001" not in p_ids # 1200 kg capacity
    assert "LP003" not in p_ids # 600 kg capacity

    # Extremely large load exceeding all partner capacities (10,000 kg)
    heavy_matches = match_logistics_partners(
        required_quantity_kg=10000.0,
        origin="Nashik",
        destination="Pune",
        partners_df=mock_partners_df,
    )
    assert len(heavy_matches) == 0


def test_unavailable_partner_exclusion(mock_partners_df):
    """Test 3: Excludes partners whose status is not 'Available'."""
    matches = match_logistics_partners(
        required_quantity_kg=500.0,
        origin="Nashik",
        destination="Pune",
        only_available=True,
        partners_df=mock_partners_df,
    )

    for m in matches:
        assert m["availability"].lower() == "available"
        assert m["partner_id"] != "LP004"


def test_service_area_matching(mock_partners_df):
    """Test 4: Matches partners that service the origin or destination corridor."""
    # Ahmednagar to Pune: LP003 is based in Ahmednagar and services Pune
    matches = match_logistics_partners(
        required_quantity_kg=400.0,
        origin="Ahmednagar",
        destination="Pune",
        partners_df=mock_partners_df,
    )

    p_ids = [m["partner_id"] for m in matches]
    assert "LP003" in p_ids


def test_freight_calculation(mock_partners_df):
    """Test 5: Validates exact freight calculation using distance and rates."""
    matches = match_logistics_partners(
        required_quantity_kg=500.0,
        origin="Nashik",
        destination="Pune",
        partners_df=mock_partners_df,
    )

    # Nashik to Pune distance is 210 km
    lp001_match = next(m for m in matches if m["partner_id"] == "LP001")
    assert lp001_match["distance_km"] == 210.0
    # Base cost 500 + 210 * 28 = 500 + 5880 = 6380.0
    assert lp001_match["estimated_freight"] == 6380.0
    assert lp001_match["freight_per_kg"] == round(6380.0 / 500.0, 2) # 12.76
    assert lp001_match["network_type"] == "Prototype logistics partner network"


def test_assignment_and_persistence():
    """Test 6: Assigns a partner to a transaction and stores in CSV."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
        temp_path = tf.name

    try:
        assign_res = assign_partner_to_transaction(
            partner_id="LP001",
            transaction_id="TX_TEST_99",
            pickup_location="Niphad, Nashik",
            destination="Pune Hub",
            quantity_kg=500.0,
            estimated_freight=6380.0,
            vehicle="Mini Truck",
            status="Assigned",
            assignments_file=temp_path,
        )

        assert assign_res["transaction_id"] == "TX_TEST_99"
        assert assign_res["partner_id"] == "LP001"
        assert assign_res["status"] == "Assigned"
        assert assign_res["estimated_freight"] == 6380.0

        # Load back
        df_loaded = load_partner_assignments(temp_path)
        assert len(df_loaded) == 1
        assert df_loaded.iloc[0]["transaction_id"] == "TX_TEST_99"
        assert df_loaded.iloc[0]["status"] == "Assigned"

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_status_transitions():
    """Test 7: Validates lifecycle status transitions."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
        temp_path = tf.name

    try:
        # 1. Create initial assignment
        assign_partner_to_transaction(
            partner_id="LP001",
            transaction_id="TX_LIFECYCLE_01",
            pickup_location="Niphad, Nashik",
            destination="Pune",
            status="Requested",
            assignments_file=temp_path,
        )

        # 2. Transition to Assigned
        up1 = update_partner_assignment_status("TX_LIFECYCLE_01", "Assigned", assignments_file=temp_path)
        assert up1["status"] == "Assigned"

        # 3. Transition to Pickup Scheduled
        up2 = update_partner_assignment_status("TX_LIFECYCLE_01", "Pickup Scheduled", assignments_file=temp_path)
        assert up2["status"] == "Pickup Scheduled"

        # 4. Transition to In Transit
        up3 = update_partner_assignment_status("TX_LIFECYCLE_01", "In Transit", assignments_file=temp_path)
        assert up3["status"] == "In Transit"

        # 5. Transition to Delivered
        up4 = update_partner_assignment_status("TX_LIFECYCLE_01", "Delivered", assignments_file=temp_path)
        assert up4["status"] == "Delivered"

        # 6. Invalid status rejected
        up_invalid = update_partner_assignment_status("TX_LIFECYCLE_01", "InvalidStatusXYZ", assignments_file=temp_path)
        assert up_invalid is None

        # 7. Cancelled transition test on separate transaction
        assign_partner_to_transaction(
            partner_id="LP002",
            transaction_id="TX_CANCEL_02",
            pickup_location="Nashik",
            destination="Mumbai",
            status="Requested",
            assignments_file=temp_path,
        )
        up_cancel = update_partner_assignment_status("TX_CANCEL_02", "Cancelled", assignments_file=temp_path)
        assert up_cancel["status"] == "Cancelled"

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
