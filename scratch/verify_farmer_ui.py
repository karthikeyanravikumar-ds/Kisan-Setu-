import sys
import os
sys.path.insert(0, os.path.abspath("."))
import re
import pandas as pd
from utils.translations import TRANSLATIONS, t, get_current_language
from utils.data_loader import load_produce, load_farmers, load_buyers, load_transactions
from utils.consumer_orders import load_consumer_orders

print("=" * 60)
print("VERIFYING FARMER UI & TRANSLATIONS")
print("=" * 60)

farmer_pages = [
    "pages/farmer.py",
    "pages/list_produce.py",
    "pages/farmer_orders.py",
    "pages/digital_mandi.py",
]

missing_keys = {"English": set(), "Hindi": set(), "Marathi": set()}

key_pattern = re.compile(r"""\bt\(\s*["']([a-zA-Z0-9_-]+)["']""")

for page in farmer_pages:
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
    print("\n[PERFECT] ZERO missing translation keys across all Farmer pages!")

print("\nVerifying datasets...")
p_df = load_produce()
f_df = load_farmers()
b_df = load_buyers()
t_df = load_transactions()
c_df = load_consumer_orders()
print(f"Produce count: {len(p_df)}")
print(f"Farmers count: {len(f_df)}")
print(f"Buyers count: {len(b_df)}")
print(f"Transactions count: {len(t_df)}")
print(f"Consumer orders count: {len(c_df)}")

print("\nVerification complete.")
