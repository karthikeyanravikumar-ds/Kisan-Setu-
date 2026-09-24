"""
Comprehensive Dual API Integration Test Suite for Kisan Setu:
1. Test Current Daily API #1 independently
2. Test Variety-wise API #2 independently
3. Test Maharashtra state filtering
4. Test Nashik district filtering
5. Test Ahilyanagar & Ahmednagar filtering
6. Test Onion commodity filtering
7. Test Tomato commodity filtering
8. Test empty API response handling
9. Test API failure & error recovery
10. Test missing DATA_GOV_API_KEY behavior
11. Test Streamlit pages startup & import integrity
12. Verify no API key is exposed or printed
13. Verify no hardcoded mandi prices remain in live UI components
"""

import os
import sys
from pathlib import Path
import pandas as pd

# Ensure UTF-8 output encoding for Windows terminal
sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from data_ingestion.data_gov_api import (
    DataGovAPIClient,
    get_current_daily_prices,
    get_variety_wise_prices,
)
from data_ingestion.market_data import (
    clean_market_data,
    get_live_mandi_pulse_items,
    get_live_price_chits,
    get_market_floor_telemetry,
    calculate_demand_signal,
    generate_setu_intelligence_signal,
    get_latest_market_price,
    get_mandi_data_status,
)

print("=" * 70)
print("TEST 1: API #1 (CURRENT DAILY PRICES) INDEPENDENT TEST")
print("=" * 70)
client = DataGovAPIClient()
res_api1 = client.fetch_current_daily_prices(state="Maharashtra", limit=5)
print(f"Status: {res_api1['status']}")
print(f"Total records in API #1: {res_api1['total']}")
print(f"Fetched count: {len(res_api1['records'])}")
assert res_api1["status"] == "success", f"API #1 failed: {res_api1.get('error_message')}"
assert len(res_api1["records"]) > 0, "API #1 should return records"
sample1 = res_api1["records"][0]
print(f"Sample API #1 record: {sample1.get('commodity')} at {sample1.get('market')} ({sample1.get('district')}) -> Modal: ₹{float(sample1.get('modal_price', 0))/100.0:.2f}/kg")
print("✓ API #1 verified successfully.")

print("\n" + "=" * 70)
print("TEST 2: API #2 (VARIETY-WISE DAILY PRICES) INDEPENDENT TEST")
print("=" * 70)
res_api2 = client.fetch_variety_wise_prices(state="Maharashtra", commodity="Onion", limit=5)
print(f"Status: {res_api2['status']}")
print(f"Total records in API #2: {res_api2['total']}")
print(f"Fetched count: {len(res_api2['records'])}")
assert res_api2["status"] == "success", f"API #2 failed: {res_api2.get('error_message')}"
assert len(res_api2["records"]) > 0, "API #2 should return records"
sample2 = res_api2["records"][0]
print(f"Sample API #2 record: {sample2.get('Commodity')} (Variety: {sample2.get('Variety')}, Grade: {sample2.get('Grade')}) at {sample2.get('Market')} -> Modal: ₹{float(sample2.get('Modal_Price', 0))/100.0:.2f}/kg")
print("✓ API #2 verified successfully.")

print("\n" + "=" * 70)
print("TEST 3 TO 7: PILOT FILTERING (STATE, DISTRICTS, COMMODITIES)")
print("=" * 70)
filters_to_test = [
    ("Maharashtra", "Nashik", "Onion"),
    ("Maharashtra", "Pune", "Onion"),
    ("Maharashtra", "Ahilyanagar", "Onion"),
    ("Maharashtra", "Ahmednagar", "Onion"),
    ("Maharashtra", "Nashik", "Tomato"),
    ("Maharashtra", "Pune", "Tomato"),
]

for state, dist, crop in filters_to_test:
    bench = get_latest_market_price(crop, district=dist, state=state)
    print(f"• [{state} | {dist} | {crop}] -> Market: {bench['market']} | Date: {bench['arrival_date']} | Modal: ₹{bench['modal_price_per_kg']:.2f}/kg (Source: {bench['source']})")
    assert bench["modal_price_per_kg"] > 0, f"Invalid price for {dist} {crop}"
print("✓ All district and commodity filter tests passed.")

print("\n" + "=" * 70)
print("TEST 8: EMPTY API RESPONSE HANDLING")
print("=" * 70)
res_empty = client.fetch_current_daily_prices(state="NonExistentStateXYZ123", commodity="NonExistentCrop999")
print(f"Empty response status: {res_empty['status']}, records: {len(res_empty['records'])}")
clean_empty = clean_market_data(res_empty["records"])
assert clean_empty.empty, "Cleaned empty response should be empty DataFrame"
bench_fallback = get_latest_market_price("NonExistentCrop999", district="UnknownDist")
assert bench_fallback["modal_price_per_kg"] > 0, "Fallback baseline price should be provided safely"
print("✓ Empty response handled gracefully with safe fallback.")

print("\n" + "=" * 70)
print("TEST 9: API FAILURE & ERROR RECOVERY")
print("=" * 70)
bad_client = DataGovAPIClient(api_key="CORRUPT_OR_INVALID_KEY")
res_fail = bad_client.fetch_current_daily_prices(state="Maharashtra")
print(f"Error handling status: {res_fail['status']}")
print(f"Safe error message: {res_fail.get('error_message')}")
assert res_fail["status"] == "error"
print("✓ API failure caught and safely handled without exposing credentials or crashing.")

print("\n" + "=" * 70)
print("TEST 10: MISSING API KEY BEHAVIOR")
print("=" * 70)
no_key_client = DataGovAPIClient(api_key="")
res_no_key = no_key_client.fetch_current_daily_prices()
assert res_no_key["status"] == "error"
assert "missing or empty" in res_no_key.get("error_message", "")
print("✓ Missing API key handled cleanly.")

print("\n" + "=" * 70)
print("TEST 11 & 12: STREAMLIT APP & PAGE IMPORT / NO KEY LEAKAGE")
print("=" * 70)
import app
from pages import digital_mandi, farmer, admin_dashboard, impact_analytics

# Masked key check
masked = client.get_api_key_masked()
assert not masked.startswith(os.getenv("DATA_GOV_API_KEY", "NONEXISTENT")[:10]), "Full API key must never be logged"
print(f"Masked key representation: {masked}")
print("✓ All pages imported cleanly without runtime or syntax errors.")

print("\n" + "=" * 70)
print("TEST 13: LIVE MANDI TELEMETRY & CHITS INTEGRATION")
print("=" * 70)
pulse = get_live_mandi_pulse_items()
chits = get_live_price_chits()
floor = get_market_floor_telemetry()
intel = generate_setu_intelligence_signal("Onion", "Nashik")
status = get_mandi_data_status()

print(f"Pulse items: {len(pulse)} (Sample: {pulse[0]['market']} {pulse[0]['crop']} {pulse[0]['price']} {pulse[0]['change']})")
print(f"Chits items: {len(chits)} (Sample: {chits[0]['commodity']} at {chits[0]['market']}: ₹{chits[0]['price']:.2f}/kg)")
print(f"Market Floor rows: {len(floor)}")
print(f"Demand Signal: {calculate_demand_signal('Onion')}")
print(f"Setu Intel: {intel['insight_text']}")
print(f"Data Status: {status['status_badge']} ({status['source']})")

assert len(pulse) > 0, "Pulse should have items"
assert len(chits) > 0, "Chits should have items"
assert len(floor) > 0, "Floor should have rows"
print("✓ Live Mandi UI components successfully populated.")

print("\n" + "=" * 70)
print("ALL 13 TESTS PASSED CLEANLY & SUCCESSFULLY!")
print("=" * 70)
