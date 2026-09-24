import sys
import io
import pandas as pd
from pathlib import Path

# Fix Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from utils.translations import t, TRANSLATIONS
from pages.list_produce import get_produce_photos, check_active_transactions

def test_phase_5d_translations_and_keys():
    keys_to_test = [
        "brand_list_produce_title", "brand_list_produce_sub", "badge_lot_gen",
        "view", "edit", "delete", "delete_harvest_lot", "cancel",
        "delete_lot_btn", "product_photo", "no_product_photo",
        "view_details", "edit_harvest_lot", "save_changes",
        "changes_saved", "lot_deleted", "cannot_delete",
        "active_transaction_warn", "confirm_deletion_title",
        "confirm_deletion_warning", "btn_create_new_lot",
        "my_harvest_lots", "filter_by_crop", "all_crops", "search",
        "search_lots_placeholder", "available_volume_label", "best_opportunity_label",
        "active_lots_label", "top_crop_label", "crop_quantity_summary",
        "back_to_lots", "existing_photos_label",
        "upload_new_photo_label", "lot_details_title", "ai_match_badge",
        "potential_spread"
    ]
    
    languages = ["English", "Hindi", "Marathi"]
    for lang in languages:
        for key in keys_to_test:
            val = t(key, language=lang, crop="Onion", qty="500", lot_id="P001", count=2)
            assert val != key, f"Missing translation for key '{key}' in language '{lang}'"
            assert isinstance(val, str) and len(val) > 0
            # Ensure no double quotes or broken templates
            assert "{" not in val or key in ["crop_quantity_summary", "active_bidders", "available_harvest", "grade_label", "produce_listed_success", "active_orders_count_label", "items_in_fulfilment_label"]
    print("[PASS] All Phase 5D polished translations verified across English, Hindi, Marathi.")

def test_language_purity():
    # English title must NOT contain Marathi or Devanagari script
    en_title = t("brand_list_produce_title", language="English")
    assert "शेतमाल" not in en_title, f"English title should not contain Marathi: {en_title}"
    assert "LIST PRODUCE" in en_title
    
    # Marathi title must be native
    mr_title = t("brand_list_produce_title", language="Marathi")
    assert "शेतमाल" in mr_title
    
    # Hindi title must be native
    hi_title = t("brand_list_produce_title", language="Hindi")
    assert "उपज" in hi_title
    print("[PASS] Language purity confirmed: English, Marathi, Hindi are distinct without undesirable string mixing.")

def test_button_translations():
    # View, Edit, Delete
    assert t("view", language="English") == "VIEW"
    assert t("edit", language="English") == "EDIT"
    assert t("delete", language="English") == "DELETE"
    
    assert t("view", language="Marathi") == "पहा"
    assert t("edit", language="Marathi") == "संपादित करा"
    assert t("delete", language="Marathi") == "हटवा"
    
    assert t("view", language="Hindi") == "देखें"
    assert t("edit", language="Hindi") == "संपादित करें"
    assert t("delete", language="Hindi") == "हटाएं"
    print("[PASS] Action button translations verified across all 3 languages.")

def test_no_photo_translations():
    assert t("no_product_photo", language="English") == TRANSLATIONS["English"]["no_product_photo"]
    assert t("no_product_photo", language="Marathi") == TRANSLATIONS["Marathi"]["no_product_photo"]
    assert t("no_product_photo", language="Hindi") == TRANSLATIONS["Hindi"]["no_product_photo"]
    print("[PASS] No photo placeholders verified across all 3 languages.")

def test_photos():
    photos_p007 = get_produce_photos("P007")
    assert len(photos_p007) > 0, "P007 should have photos"
    photos_nonexistent = get_produce_photos("P999999")
    assert len(photos_nonexistent) == 0
    print("[PASS] Photo retrieval logic verified.")

def test_active_transaction_protection():
    has_active_p001, txs_p001 = check_active_transactions("P001")
    assert has_active_p001 is True, "P001 should have active transactions!"
    assert len(txs_p001) > 0
    has_active_fake, txs_fake = check_active_transactions("P999999")
    assert has_active_fake is False
    assert len(txs_fake) == 0
    print("[PASS] Active transaction protection properly detected active orders for P001 and allowed non-active.")

if __name__ == "__main__":
    test_phase_5d_translations_and_keys()
    test_language_purity()
    test_button_translations()
    test_no_photo_translations()
    test_photos()
    test_active_transaction_protection()
    print("[SUCCESS] ALL PHASE 5D POLISH TESTS PASSED SUCCESSFULLY!")
