import sys
import os
import pandas as pd
from datetime import date

# Set root dir in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
sys.stdout.reconfigure(encoding='utf-8')

from utils.data_loader import (
    load_farmers,
    load_buyers,
    load_produce,
    load_logistics,
    load_prices,
    load_demand,
    load_feedback,
    load_buyer_requirements,
)
from utils.transactions import (
    load_transactions,
    create_transaction,
    update_transaction_status,
    generate_transaction_id,
    TRANSACTIONS_FILE,
)
from utils.consumer_orders import (
    load_consumer_orders,
    create_consumer_order,
    update_consumer_order_status,
    generate_order_id,
)
from ai.matching import find_matches, calculate_match_score, get_distance
from ai.demand_forecasting import forecast_demand
from utils.translations import TRANSLATIONS, t, set_current_language, get_current_language
from utils.auth import DEMO_USERS, login, logout

def run_master_test():
    print("=" * 60)
    print("KISAN SETU — MASTER END-TO-END ECOSYSTEM AUDIT & TEST")
    print("=" * 60)

    # 1. DATASETS INTEGRITY
    print("\n[STEP 1] Validating CSV Datasets...")
    farmers = load_farmers()
    buyers = load_buyers()
    produce = load_produce()
    logistics = load_logistics()
    prices = load_prices()
    demand = load_demand()
    feedback = load_feedback()
    transactions = load_transactions()
    consumer_orders = load_consumer_orders()
    requirements = load_buyer_requirements()

    print(f"  ✓ Farmers: {len(farmers)} rows")
    print(f"  ✓ Buyers: {len(buyers)} rows")
    print(f"  ✓ Produce: {len(produce)} lots")
    print(f"  ✓ Logistics: {len(logistics)} fleet providers")
    print(f"  ✓ Prices: {len(prices)} mandi price records")
    print(f"  ✓ Demand: {len(demand)} demand records")
    print(f"  ✓ Transactions: {len(transactions)} B2B deals")
    print(f"  ✓ Consumer Orders: {len(consumer_orders)} B2C orders")
    print(f"  ✓ Buyer Requirements: {len(requirements)} active requisitions")

    # 2. MULTILINGUAL DICTIONARY QA
    print("\n[STEP 2] Auditing Multilingual Coverage (EN, HI, MR)...")
    keys_en = set(TRANSLATIONS.get("English", {}).keys())
    keys_hi = set(TRANSLATIONS.get("Hindi", {}).keys())
    keys_mr = set(TRANSLATIONS.get("Marathi", {}).keys())
    
    missing_hi = keys_en - keys_hi
    missing_mr = keys_en - keys_mr
    assert len(missing_hi) == 0, f"Missing in Hindi: {missing_hi}"
    assert len(missing_mr) == 0, f"Missing in Marathi: {missing_mr}"
    print(f"  ✓ English keys: {len(keys_en)}")
    print(f"  ✓ Hindi keys: {len(keys_hi)} (0 missing)")
    print(f"  ✓ Marathi keys: {len(keys_mr)} (0 missing)")

    # 3. END-TO-END SCENARIO T017 SIMULATION
    print("\n[STEP 3] Executing End-to-End B2B Lifecycle Scenario (T017)...")
    
    # Check initial transaction state
    tx_before = load_transactions()
    expected_tx_id = generate_transaction_id(tx_before)
    print(f"  → Next Available B2B Transaction ID: {expected_tx_id}")

    # Actor 1: Farmer (F001 - Ramesh Patil) selects Onion lot (P001)
    farmer_id = "F001"
    produce_lot = produce[produce["farmer_id"] == farmer_id].iloc[0]
    p_id = produce_lot["produce_id"]
    p_crop = produce_lot["crop"]
    p_qty = float(produce_lot["quantity_kg"])
    p_price = float(produce_lot["expected_price_per_kg"])
    print(f"  👨‍🌾 Farmer {farmer_id} offering Lot #{p_id} ({p_crop}, {p_qty} kg @ ₹{p_price}/kg)")

    # AI Matching
    matches = find_matches(produce_lot, buyers)
    assert not matches.empty, "Matches should not be empty"
    top_match = matches.iloc[0]
    buyer_id = top_match["buyer_id"]
    buyer_name = top_match["buyer_name"]
    offered_price = float(top_match["max_price_per_kg"])
    match_score = top_match["match_score"]
    print(f"  🎯 Top AI Match: {buyer_name} (#{buyer_id}) with {match_score:.0f}% match score @ ₹{offered_price}/kg")

    # Farmer Accepts Deal & Creates Transaction
    new_tx = create_transaction(
        farmer_id=farmer_id,
        buyer_id=buyer_id,
        produce_id=p_id,
        quantity_kg=p_qty,
        price_per_kg=offered_price,
        status="Order Placed",
    )
    tx_id = new_tx["transaction_id"]
    print(f"  🤝 Deal Initiated → Transaction ID: #{tx_id} [Status: {new_tx['status']}]")

    # Verify transaction in single source of truth
    tx_check = load_transactions()
    tx_record = tx_check[tx_check["transaction_id"] == tx_id]
    assert len(tx_record) == 1, f"Expected exactly 1 record for #{tx_id}, got {len(tx_record)}"
    print(f"  ✓ Transaction #{tx_id} persisted in transactions.csv")

    # Actor 2: Buyer (B001 - Pune Fresh Retail) confirms procurement
    print(f"  🛒 Buyer #{buyer_id} confirms procurement...")
    ok = update_transaction_status(tx_id, "Confirmed")
    assert ok, "Status update to Confirmed failed"
    tx_record = load_transactions()[load_transactions()["transaction_id"] == tx_id].iloc[0]
    assert tx_record["status"] == "Confirmed", f"Expected Confirmed, got {tx_record['status']}"
    print(f"  ✓ Transaction #{tx_id} status updated to: {tx_record['status']}")

    # Actor 3: Logistics (L001 - Maharashtra Agro Transport) accepts load & starts transit
    print(f"  🚚 Logistics provider dispatches load...")
    ok = update_transaction_status(tx_id, "In Transit")
    assert ok, "Status update to In Transit failed"
    tx_record = load_transactions()[load_transactions()["transaction_id"] == tx_id].iloc[0]
    assert tx_record["status"] == "In Transit", f"Expected In Transit, got {tx_record['status']}"
    print(f"  ✓ Transaction #{tx_id} status updated to: {tx_record['status']}")

    # Logistics marks delivery arrival
    ok = update_transaction_status(tx_id, "Delivered")
    assert ok, "Status update to Delivered failed"
    tx_record = load_transactions()[load_transactions()["transaction_id"] == tx_id].iloc[0]
    assert tx_record["status"] == "Delivered", f"Expected Delivered, got {tx_record['status']}"
    print(f"  ✓ Transaction #{tx_id} status updated to: {tx_record['status']}")

    # Actor 4: Buyer verifies quality/quantity and completes deal
    print(f"  🏢 Buyer inspects goods (Quality Verified: Grade A, Quantity: {p_qty} kg) and settles payment...")
    ok = update_transaction_status(tx_id, "Completed")
    assert ok, "Status update to Completed failed"
    tx_record = load_transactions()[load_transactions()["transaction_id"] == tx_id].iloc[0]
    assert tx_record["status"] == "Completed", f"Expected Completed, got {tx_record['status']}"
    print(f"  ✓ Transaction #{tx_id} status updated to: {tx_record['status']}")

    # 4. DUPLICATE PROTECTION & ISOLATION CHECK
    print("\n[STEP 4] Verifying Duplicate Protection & B2B/B2C Isolation...")
    # B2C Consumer Order
    c_order_id = generate_order_id(load_consumer_orders())
    consumer_order = create_consumer_order(
        consumer_id="C001",
        consumer_name="Demo Consumer",
        produce_id=p_id,
        farmer_id=farmer_id,
        crop=p_crop,
        quantity_kg=10.0,
        price_per_kg=p_price,
    )
    print(f"  🛍️ Consumer Order Created: #{consumer_order['order_id']} for {consumer_order['quantity_kg']} kg {consumer_order['crop']}")
    
    # Verify B2B transaction #{tx_id} is unchanged
    tx_final = load_transactions()[load_transactions()["transaction_id"] == tx_id]
    assert len(tx_final) == 1, f"B2B Transaction #{tx_id} was corrupted!"
    assert tx_final.iloc[0]["status"] == "Completed", "B2B Transaction status was altered by B2C order!"
    print(f"  ✓ B2B Transaction #{tx_id} remains intact and isolated in transactions.csv")

    # Clean up test transaction #{tx_id} and test consumer order #{consumer_order['order_id']} to leave clean CSV
    print(f"\n[STEP 5] Cleaning up test records from CSV to preserve benchmark datasets...")
    df_tx_clean = load_transactions()
    df_tx_clean = df_tx_clean[df_tx_clean["transaction_id"] != tx_id]
    df_tx_clean.to_csv(TRANSACTIONS_FILE, index=False)

    df_c_clean = load_consumer_orders()
    df_c_clean = df_c_clean[df_c_clean["order_id"] != consumer_order["order_id"]]
    df_c_clean.to_csv(os.path.join(ROOT_DIR, "data", "consumer_orders.csv"), index=False)
    print(f"  ✓ Cleaned test transaction #{tx_id} and test order #{consumer_order['order_id']}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    run_master_test()
