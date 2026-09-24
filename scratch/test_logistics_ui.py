import sys
import os
sys.path.insert(0, os.path.abspath("."))
import re
import pandas as pd
from utils.translations import TRANSLATIONS, t, get_current_language
from utils.data_loader import (
    load_logistics,
    load_produce,
    load_buyers,
    load_farmers,
    load_transactions,
)
from ai.matching import get_distance

print("=" * 60)
print("VERIFYING LOGISTICS UI & TRANSLATIONS")
print("=" * 60)

logistics_pages = [
    "pages/logistics.py",
]

missing_keys = {"English": set(), "Hindi": set(), "Marathi": set()}
key_pattern = re.compile(r"""\bt\(\s*["']([a-zA-Z0-9_-]+)["']""")

for page in logistics_pages:
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
    print("\n[PERFECT] ZERO missing translation keys across Logistics page!")

print("\nVerifying Logistics data loading...")
logistics_df = load_logistics()
transactions_df = load_transactions()
print(f"Fleet providers: {len(logistics_df)}")
print(f"Total transactions: {len(transactions_df)}")

active_txs = transactions_df[transactions_df["status"].astype(str).isin(["Order Placed", "Confirmed", "In Transit"])]
print(f"Active deliveries: {len(active_txs)}")

print("\nLogistics UI Verification Complete!")
