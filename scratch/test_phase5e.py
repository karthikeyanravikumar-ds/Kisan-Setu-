import sys
import io
import pandas as pd
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from utils.translations import t, TRANSLATIONS
from utils.data_loader import load_produce, load_buyers, load_demand, load_prices, load_logistics
from ai.matching import find_matches
from ai.demand_forecasting import forecast_demand
from gemini.explanation import explain_buyer_match
from utils.transactions import create_transaction, load_transactions

def test_phase_5e_translations():
    keys_to_test = [
        "ai_market_match_title", "ai_market_match_sub", "selected_lot_label",
        "best_available_opportunity_title", "recommended_match_badge",
        "mandi_reference_price", "potential_realization_label",
        "no_suitable_match_title", "no_suitable_match_desc", "btn_view_digital_mandi",
        "why_this_buyer_title", "why_kisan_setu_recommends_buyer",
        "factor_qty_reason", "factor_qual_reason", "factor_price_reason",
        "factor_demand_reason", "factor_distance_reason", "factor_timing_reason",
        "rating_strong", "rating_good", "rating_high",
        "buyer_info_title", "buyer_name_label", "buyer_type_label",
        "buyer_location_label", "buyer_required_qty_label", "buyer_min_quality_label",
        "buyer_max_price_label", "buyer_demand_label",
        "price_intelligence_title", "mandi_benchmark_label", "buyer_offer_label",
        "potential_spread_label", "potential_difference_total",
        "delivery_logistics_title", "estimated_distance_label", "estimated_freight_label",
        "net_realization_label", "btn_view_route", "btn_hide_route",
        "btn_select_this_buyer", "confirm_deal_title", "confirm_deal_subtitle",
        "btn_cancel_deal", "btn_confirm_create_order",
        "order_initiated_success_title", "order_initiated_success_desc",
        "btn_view_active_order", "available_buyer_matches_title",
        "other_matches_count_label", "kisan_bol_match_prompt"
    ]
    
    languages = ["English", "Hindi", "Marathi"]
    for lang in languages:
        for key in keys_to_test:
            val = t(key, language=lang, qty=500, req_qty=600, farmer_grade="A", buyer_grade="A", buyer_price="31.00", expected_price="30.00", distance=145, count=3)
            assert val != key, f"Missing translation for key '{key}' in language '{lang}'"
            assert isinstance(val, str) and len(val) > 0
    print("[PASS] All 50 Phase 5E translations verified across English, Hindi, Marathi.")

def test_matching_pipeline():
    produce_df = load_produce()
    buyers_df = load_buyers()
    demand_df = load_demand()
    
    sample_lot = produce_df.iloc[0]
    forecast = forecast_demand(demand_df=demand_df, district="Pune", crop=sample_lot["crop"], forecast_days=3)
    forecast_kg = forecast["forecast_demand_kg"] if forecast is not None else None
    
    matches = find_matches(sample_lot, buyers_df, forecast_demand=forecast_kg)
    assert not matches.empty, "Matches should not be empty for sample Onion lot"
    top_match = matches.iloc[0]
    assert "match_score" in top_match
    assert "buyer_name" in top_match
    assert "max_price_per_kg" in top_match
    print(f"[PASS] Matching pipeline verified: Top match is {top_match['buyer_name']} with score {top_match['match_score']}%.")

def test_gemini_multilingual_explanation():
    languages = ["English", "Hindi", "Marathi"]
    for lang in languages:
        explanation = explain_buyer_match(
            crop="Onion",
            quantity=500,
            quality="A",
            farmer_location="Niphad, Nashik",
            buyer_name="Pune Fresh Retail",
            buyer_type="Retailer",
            buyer_quantity=550,
            buyer_price=38.0,
            distance=145.0,
            match_score=94.0,
            language=lang,
        )
        assert len(explanation) > 50, f"Explanation too short for {lang}"
        print(f"[PASS] Gemini explanation generated for {lang} ({len(explanation)} chars).")

def test_no_match_scenario():
    buyers_df = load_buyers()
    fake_produce = pd.Series({
        "produce_id": "P_FAKE",
        "farmer_id": "F001",
        "crop": "ExoticDragonFruitNotFound",
        "quantity_kg": 100,
        "quality_grade": "A",
        "location": "Niphad",
        "district": "Nashik",
        "available_date": "2026-09-10",
        "expected_price_per_kg": 200,
        "status": "Available"
    })
    matches = find_matches(fake_produce, buyers_df)
    assert matches.empty, "Fake produce should return 0 matches"
    print("[PASS] No-match empty state logic verified.")

if __name__ == "__main__":
    test_phase_5e_translations()
    test_matching_pipeline()
    test_gemini_multilingual_explanation()
    test_no_match_scenario()
    print("[SUCCESS] ALL PHASE 5E TESTS PASSED SUCCESSFULLY!")
