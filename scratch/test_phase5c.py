import os
import sys

# Ensure UTF-8 output encoding
sys.stdout.reconfigure(encoding='utf-8')

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.translations import TRANSLATIONS, t, set_current_language
from utils.data_loader import (
    load_demand, load_produce, load_buyers, load_logistics, load_prices, load_farmers, load_transactions
)
from ai.matching import find_matches
from gemini.explanation import explain_buyer_match

print("=== 1. VERIFYING ALL PHASE 5C TRANSLATION KEYS ===")
phase_5c_keys = [
    'farmer_hub_header_title', 'good_morning_user', 'pilot_region',
    'what_should_you_do_today', 'best_available_opp', 'additional_realization_label',
    'btn_find_buyer', 'btn_ask_kisan_bol', 'why_this_action_title',
    'why_kisan_setu_recommends', 'factor_price_compat', 'factor_qty_compat',
    'factor_quality_compat', 'factor_distance', 'factor_demand', 'factor_timing',
    'market_snapshot_title', 'current_mandi_price', 'best_buyer_realization',
    'potential_spread', 'demand_confidence', 'my_harvest_title',
    'active_lots_label', 'available_qty_label', 'best_lot_label',
    'btn_view_my_harvest', 'active_orders_title', 'in_fulfilment_label',
    'completed_orders_label', 'b2b_deals_label', 'b2c_orders_label',
    'btn_view_active_orders', 'need_help_title', 'ask_kisan_bol_prompt',
    'kb_prompt_1', 'kb_prompt_2', 'kb_prompt_3', 'kb_prompt_4'
]

for lang in ['English', 'Marathi', 'Hindi']:
    set_current_language(lang)
    for k in phase_5c_keys:
        val = t(k, name="Ramesh", id="F001", location="Niphad, Nashik", count=2)
        assert val != k, f"Missing translation for key '{k}' in {lang}"
        assert not val.startswith("{") and not val.endswith("}"), f"Raw key detected for '{k}' in {lang}: {val}"
print("✓ All 38 Phase 5C translation keys verified across English, Marathi, and Hindi.")

print("\n=== 2. VERIFYING FARMER OVERVIEW DATA & MATCHING INTEGRITY ===")
produce = load_produce()
buyers = load_buyers()
farmers = load_farmers()
prices = load_prices()
transactions = load_transactions()

f_produce = produce[produce["farmer_id"] == "F001"]
assert len(f_produce) > 0, f"Expected produce lots for F001, got {len(f_produce)}"
p001 = f_produce.iloc[0]

matches = find_matches(p001, buyers)
assert not matches.empty, "No buyer matches found for P001"
best = matches.iloc[0]

print(f"Active Lots for F001: {len(f_produce)}")
print(f"Total Available Quantity: {int(f_produce['quantity_kg'].sum()):,} kg")
print(f"Top Match: {best['buyer_name']} ({best['match_score']:.1f}% match, offer: ₹{best['max_price_per_kg']}/kg)")

print("\n=== 3. VERIFYING ALL REFERENCED ROUTES ON DISK ===")
routes = [
    "pages/farmer.py",
    "pages/list_produce.py",
    "pages/farmer_orders.py",
    "pages/digital_mandi.py",
    "pages/impact_analytics.py",
    "pages/government_schemes.py",
    "pages/sms_services.py"
]
for r in routes:
    fp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), r)
    assert os.path.exists(fp), f"Route file missing: {r}"
print("✓ All 7 Farmer journey routes verified on disk.")

print("\n=== ALL PHASE 5C TESTS PASSED SUCCESSFULLY! ===")
