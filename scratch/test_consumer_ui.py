import sys
import os
sys.path.insert(0, os.path.abspath("."))
import re
import pandas as pd
from utils.translations import TRANSLATIONS, t, get_current_language
from utils.data_loader import load_produce, load_farmers
from utils.consumer_orders import load_consumer_orders, create_consumer_order

print("=" * 60)
print("VERIFYING CONSUMER UI & TRANSLATIONS")
print("=" * 60)

consumer_pages = [
    "pages/consumer.py",
]

missing_keys = {"English": set(), "Hindi": set(), "Marathi": set()}
key_pattern = re.compile(r"""\bt\(\s*["']([a-zA-Z0-9_-]+)["']""")

for page in consumer_pages:
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
    print("\n[PERFECT] ZERO missing translation keys across Consumer page!")

print("\nVerifying Consumer Order workflow...")
produce_df = load_produce()
avail_p = produce_df[produce_df["status"].astype(str).str.lower() == "available"]
print(f"Available produce count: {len(avail_p)}")

orders_df = load_consumer_orders()
print(f"Existing consumer orders count: {len(orders_df)}")

print("\nConsumer UI Verification Complete!")
