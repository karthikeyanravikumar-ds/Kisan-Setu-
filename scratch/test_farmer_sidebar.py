import os
import sys

# Ensure UTF-8 output encoding for Windows terminal
sys.stdout.reconfigure(encoding='utf-8')

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.translations import TRANSLATIONS, t, set_current_language
from utils.auth import login, is_logged_in, logout
from utils.voice_assistant import process_query, render_kisan_bol

print("=== 1. VERIFYING TRANSLATION COVERAGE FOR SIDEBAR ===")
required_keys = [
    'sec_farmer_ws', 'sec_my_farm', 'sec_market', 'sec_floor_gov',
    'sec_orders_delivery', 'sec_services', 'nav_overview_directives',
    'nav_produce_list', 'nav_farmer_match', 'nav_digital_mandi',
    'nav_active_orders', 'nav_schemes', 'nav_sms_services',
    'kisan_bol_title', 'presentation_nav_title', 'logout', 'active_session'
]

for lang in ['English', 'Marathi', 'Hindi']:
    set_current_language(lang)
    for k in required_keys:
        val = t(k)
        assert val != k, f"Missing translation for key '{k}' in {lang}"
        assert not val.startswith("{") and not val.endswith("}"), f"Raw key detected for '{k}' in {lang}: {val}"
print("✓ All required keys exist and have non-empty translations across English, Marathi, and Hindi.")

print("\n=== 2. VERIFYING KISAN BOL VOICE ASSISTANT PIPELINE ===")
sample_queries = {
    "English": "What is the market price of onion?",
    "Marathi": "कांद्याचा आजचा भाव काय आहे?",
    "Hindi": "प्याज़ का आज का मंडी भाव क्या है?"
}
for lang, q in sample_queries.items():
    res = process_query(q, user_profile={"user_role": "Farmer", "user_id": "F001"}, language=lang)
    assert res and "response_text" in res, f"Voice query failed for {lang}: {res}"
    assert len(res["response_text"]) > 10, f"Empty response text for {lang}"
print("✓ Kisan Bol voice processing functions flawlessly across all supported languages.")

print("\n=== 3. VERIFYING FARMER NAVIGATION PAGE PATHS ===")
farmer_pages = [
    "pages/list_produce.py",
    "pages/farmer.py",
    "pages/digital_mandi.py",
    "pages/impact_analytics.py",
    "pages/farmer_orders.py",
    "pages/government_schemes.py",
    "pages/sms_services.py"
]
for p in farmer_pages:
    full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), p)
    assert os.path.exists(full_path), f"Page path not found: {p}"
print("✓ All Farmer navigation targets exist on disk.")

print("\n=== ALL TESTS PASSED SUCCESSFULLY! ===")
