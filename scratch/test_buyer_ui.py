import sys
import os
sys.path.insert(0, os.path.abspath("."))
import re
import pandas as pd
from utils.translations import TRANSLATIONS, t, get_current_language
from utils.data_loader import (
    load_buyers,
    load_farmers,
    load_produce,
    load_transactions,
    load_buyer_requirements,
    load_logistics,
    load_prices,
    load_demand,
)
from ai.matching import calculate_match_score, get_distance
from utils.transactions import create_transaction, update_transaction_status

print("=" * 60)
print("VERIFYING BUYER UI & TRANSLATIONS")
print("=" * 60)

buyer_pages = [
    "pages/buyer.py",
    "pages/buyer_requirements.py",
]

missing_keys = {"English": set(), "Hindi": set(), "Marathi": set()}
key_pattern = re.compile(r"""\bt\(\s*["']([a-zA-Z0-9_-]+)["']""")

for page in buyer_pages:
    with open(page, "r", encoding="utf-8") as f:
        content = f.read()
    
    found_keys = key_pattern.findall(content)
    print(f"\nScanning {page}: found {len(found_keys)} translation calls ({len(set(found_keys))} unique keys).")
    
    for k in set(found_keys):
        for lang in ["English", "Hindi", "Marathi"]:
            if k not in TRANSLATIONS[lang]:
                missing_keys[lang].add((page, k))

has_missing = False
for lang, keys in missing_keys.items():
    if keys:
        has_missing = True
        print(f"\n[!] Missing in {lang} ({len(keys)} keys):")
        for pg, k in sorted(keys):
            print(f"   - {k} (in {pg})")
    else:
        print(f"\n[OK] All keys present in {lang}!")

if not has_missing:
    print("\n[PERFECT] ZERO missing translation keys across all Buyer pages!")

print("\nTesting Buyer AI Matching...")
buyers_df = load_buyers()
produce_df = load_produce()
b001 = buyers_df[buyers_df["buyer_id"] == "B001"].iloc[0]
avail_p = produce_df[produce_df["status"].astype(str).str.lower() == "available"]

matches = []
for _, p in avail_p.iterrows():
    if str(p["crop"]).lower() == str(b001["crop"]).lower():
        dist = get_distance(p["district"], b001["district"])
        score = calculate_match_score(
            quantity=float(p["quantity_kg"]),
            buyer_quantity=float(b001["required_quantity_kg"]),
            farmer_quality=p["quality_grade"],
            buyer_quality=b001["min_quality"],
            farmer_price=float(p["expected_price_per_kg"]),
            buyer_price=float(b001["max_price_per_kg"]),
            distance=dist,
            farmer_date=p["available_date"],
            buyer_date=b001["required_date"],
        )
        matches.append((p["produce_id"], p["farmer_id"], p["crop"], p["quantity_kg"], p["expected_price_per_kg"], dist, score))

matches.sort(key=lambda x: x[6], reverse=True)
print(f"Found {len(matches)} matches for Buyer B001 ({b001['name']}):")
for m in matches[:5]:
    print(f"  - Produce #{m[0]} (Farmer {m[1]}): {m[2]} {m[3]}kg @ Rs.{m[4]}/kg | Dist: {m[5]}km | Score: {m[6]}%")

print("\nBuyer UI Verification Complete!")
