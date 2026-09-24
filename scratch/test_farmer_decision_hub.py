import os
import sys

# Ensure UTF-8 output encoding for Windows terminal
sys.stdout.reconfigure(encoding='utf-8')

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.translations import TRANSLATIONS, t, set_current_language
from utils.data_loader import (
    load_demand, load_produce, load_buyers, load_logistics, load_prices, load_farmers, load_transactions
)
from ai.matching import find_matches
from gemini.explanation import explain_buyer_match

print("=== 1. VERIFYING PHASE 5B TRANSLATION KEYS ===")
phase_5b_keys = [
    'good_morning_user', 'farmer_sub_location', 'what_should_you_do_today',
    'recommended_action_label', 'action_find_buyer', 'recommended_realization_label',
    'buyer_match_label', 'additional_realization_label', 'btn_find_buyer',
    'btn_ask_kisan_bol', 'market_snapshot_title', 'current_mandi_price',
    'best_buyer_realization', 'potential_difference', 'market_demand_level',
    'demand_high', 'my_harvest_title', 'active_lots_label',
    'total_available_label', 'top_crop_label', 'btn_view_my_harvest',
    'active_orders_title', 'active_orders_count_label', 'items_in_fulfilment_label',
    'btn_view_orders', 'why_this_recommendation_title', 'show_ai_explanation_label',
    'select_produce_lot_label'
]

for lang in ['English', 'Marathi', 'Hindi']:
    set_current_language(lang)
    for k in phase_5b_keys:
        val = t(k, name="Ramesh", id="F001", location="Niphad, Nashik", count=2)
        assert val != k, f"Missing translation for key '{k}' in {lang}"
        assert not val.startswith("{") and not val.endswith("}"), f"Raw key detected for '{k}' in {lang}: {val}"
print("✓ All 28 Phase 5B translation keys verified across English, Marathi, and Hindi.")

print("\n=== 2. VERIFYING DATA & MATCHING INTEGRITY FOR FARMER F001 ===")
produce = load_produce()
buyers = load_buyers()
farmers = load_farmers()
prices = load_prices()
transactions = load_transactions()

f_produce = produce[produce["farmer_id"] == "F001"]
assert not f_produce.empty, "Farmer F001 produce lots not found"
p001 = f_produce.iloc[0]

from ai.demand_forecasting import forecast_demand

demand = load_demand()
forecast = forecast_demand(demand, "Pune", p001["crop"], 3)
forecast_kg = forecast["forecast_demand_kg"] if forecast is not None else None

matches = find_matches(p001, buyers, forecast_demand=forecast_kg)
assert not matches.empty, "No buyer match found for lot P001"
best = matches.iloc[0]

print(f"Farmer: F001 ({p001['crop']} {p001['quantity_kg']}kg Grade {p001['quality_grade']})")
print(f"Top Match: {best['buyer_name']} ({best['match_score']:.1f}% Match, Offer: ₹{best['max_price_per_kg']}/kg)")
assert best['match_score'] >= 80, f"Expected match score >= 80, got {best['match_score']}"

print("\n=== 3. VERIFYING GEMINI MULTILINGUAL EXPLANATION ===")
for lang in ['English', 'Marathi', 'Hindi']:
    exp = explain_buyer_match(
        crop=p001['crop'],
        quantity=p001['quantity_kg'],
        quality=p001['quality_grade'],
        farmer_location=f"{p001['location']}, {p001['district']}",
        buyer_name=best['buyer_name'],
        buyer_type=best['buyer_type'],
        buyer_quantity=best['required_quantity_kg'],
        buyer_price=best['max_price_per_kg'],
        distance=best['distance_km'],
        match_score=best['match_score'],
        language=lang
    )
    assert len(exp) > 50, f"Gemini explanation failed for {lang}"
    print(f"✓ Explanation generated successfully for {lang} ({len(exp)} chars)")

print("\n=== 4. VERIFYING TARGET NAVIGATION FILES EXISTENCE ===")
target_routes = [
    "pages/farmer.py",
    "pages/list_produce.py",
    "pages/farmer_orders.py",
    "pages/digital_mandi.py",
    "pages/government_schemes.py"
]
for tr in target_routes:
    full_p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), tr)
    assert os.path.exists(full_p), f"Target file missing: {tr}"
print("✓ All linked navigation target files exist.")

print("\n=== ALL PHASE 5B TESTS PASSED CLEANLY! ===")
