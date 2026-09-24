"""
Integration Test for data.gov.in API & Market Data Ingestion Pipeline.
Tests:
1. Maharashtra + Onion
2. Maharashtra + Tomato
3. Nashik + Onion
4. Pune + Onion
5. Ahilyanagar + Onion
6. Ahmednagar + Onion
7. Local cache & fallback verification
8. Units & data integrity validation
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

from data_ingestion.data_gov_api import DataGovAPIClient
from data_ingestion.market_data import (
    clean_market_data,
    fetch_market_data,
    get_latest_market_price,
    get_market_prices,
    load_local_market_cache,
    PROCESSED_FILE_PATH,
)

print("=" * 60)
print("TEST 1: API CLIENT INITIALIZATION & MASKED KEY")
print("=" * 60)
client = DataGovAPIClient()
print(f"Has API Key: {client.has_api_key}")
print(f"Masked API Key: {client.get_api_key_masked()}")
assert client.has_api_key, "API key should be detected from .env"

print("\n" + "=" * 60)
print("TEST 2: PILOT SCOPE QUERIES (LIVE API)")
print("=" * 60)

pilot_cases = [
    ("Maharashtra", None, "Onion"),
    ("Maharashtra", None, "Tomato"),
    ("Maharashtra", "Nashik", "Onion"),
    ("Maharashtra", "Pune", "Onion"),
    ("Maharashtra", "Ahilyanagar", "Onion"),
    ("Maharashtra", "Ahmednagar", "Onion"),
    ("Maharashtra", "Nashik", "Tomato"),
]

for state, district, commodity in pilot_cases:
    dist_label = district if district else "Statewide"
    print(f"\n--- Testing: {state} | {dist_label} | {commodity} ---")
    
    result = get_latest_market_price(commodity=commodity, district=district, state=state)
    
    print(f"  • Commodity:        {result['commodity']}")
    print(f"  • District:         {result['district']}")
    print(f"  • Market:           {result['market']}")
    print(f"  • Arrival Date:     {result['arrival_date']}")
    print(f"  • Variety:          {result['variety']}")
    print(f"  • Grade:            {result['grade']}")
    print(f"  • Modal Price:      ₹{result['modal_price_per_kg']:.2f}/kg  (Source: ₹{result['modal_price']:.2f}/qtl)")
    print(f"  • Min Price:        ₹{result['min_price_per_kg']:.2f}/kg  (Source: ₹{result['min_price']:.2f}/qtl)")
    print(f"  • Max Price:        ₹{result['max_price_per_kg']:.2f}/kg  (Source: ₹{result['max_price']:.2f}/qtl)")
    print(f"  • Provenance:       {result['source']} (is_live: {result['is_live']})")
    
    assert result["modal_price_per_kg"] > 0, "Modal price per kg should be positive"
    assert result["modal_price"] > 0, "Source modal price should be positive"
    assert result["source_unit"] == "Rs/Quintal" or result["source_unit"] == "Rs/kg"
    assert result["display_unit"] == "Rs/kg"

print("\n" + "=" * 60)
print("TEST 3: NORMALIZATION & DEDUPLICATION INTEGRITY")
print("=" * 60)

raw_sample = [
    {
        "Arrival_Date": "08/09/2026",
        "Commodity": "Onion",
        "Commodity_Code": "23",
        "District": "Nashik",
        "Grade": "FAQ",
        "Market": "Lasalgaon",
        "Max_Price": "3400",
        "Min_Price": "2200",
        "Modal_Price": "2850",
        "State": "Maharashtra",
        "Variety": "Red",
    },
    # Duplicate entry
    {
        "Arrival_Date": "08/09/2026",
        "Commodity": "Onion",
        "Commodity_Code": "23",
        "District": "Nashik",
        "Grade": "FAQ",
        "Market": "Lasalgaon",
        "Max_Price": "3400",
        "Min_Price": "2200",
        "Modal_Price": "2850",
        "State": "Maharashtra",
        "Variety": "Red",
    },
    # Missing / bad price row
    {
        "Arrival_Date": "08/09/2026",
        "Commodity": "Onion",
        "Commodity_Code": "23",
        "District": "Nashik",
        "Grade": "FAQ",
        "Market": "Lasalgaon",
        "Max_Price": "0",
        "Min_Price": "0",
        "Modal_Price": "0",
        "State": "Maharashtra",
        "Variety": "Red",
    }
]

cleaned = clean_market_data(raw_sample)
print(f"Cleaned records count (expected 1 after dedup and drop invalid): {len(cleaned)}")
assert len(cleaned) == 1, f"Expected 1 record, got {len(cleaned)}"
row = cleaned.iloc[0]
assert row["modal_price"] == 2850.0
assert row["modal_price_per_kg"] == 28.50
assert row["arrival_date"] == "2026-09-08"
print("✓ Deduplication, date parsing, and price unit calculation validated.")

print("\n" + "=" * 60)
print("TEST 4: LOCAL PROCESSED DATASET VERIFICATION")
print("=" * 60)
print(f"Processed file path: {PROCESSED_FILE_PATH}")
print(f"File exists: {PROCESSED_FILE_PATH.exists()}")
if PROCESSED_FILE_PATH.exists():
    df_proc = pd.read_csv(PROCESSED_FILE_PATH)
    print(f"Processed file record count: {len(df_proc)}")
    print("Sample processed records:")
    print(df_proc[["arrival_date", "commodity", "district", "market", "modal_price", "modal_price_per_kg"]].tail(3))

print("\n" + "=" * 60)
print("TEST 5: FALLBACK MECHANISM WHEN API FAILS / UNAVAILABLE")
print("=" * 60)
# Test fallback with dummy client having invalid key or dummy query
dummy_client = DataGovAPIClient(api_key="INVALID_KEY_TEST")
res_dummy = dummy_client.fetch_records(commodity="NonExistentCrop123")
print(f"Dummy client status: {res_dummy['status']}")
print(f"Error message (safe, masked): {res_dummy.get('error_message')}")
assert res_dummy["status"] == "error"

# Ensure market_data handles fallback smoothly without crashing
fallback_price = get_latest_market_price("Onion", district="Nashik")
print(f"Fallback resolution: ₹{fallback_price['modal_price_per_kg']:.2f}/kg ({fallback_price['source']})")
assert fallback_price["modal_price_per_kg"] > 0

print("\n" + "=" * 60)
print("ALL DATA.GOV.IN INTEGRATION TESTS PASSED SUCCESSFULLY!")
print("=" * 60)
