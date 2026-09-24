import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import re
from utils.translations import TRANSLATIONS

all_files = ['app.py', 'ui/theme.py', 'ui/setu_components.py', 'utils/voice_assistant.py']
for f in os.listdir('pages'):
    if f.endswith('.py'):
        all_files.append(os.path.join('pages', f))

all_keys = set()
for file_path in all_files:
    if not os.path.exists(file_path):
        continue
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Look for t("key") or t('key') with strict word boundary
    keys = re.findall(r'(?<![a-zA-Z0-9_.])t\(\s*["\']([a-zA-Z0-9_-]+)["\']\s*\)', content)
    all_keys.update(keys)

missing_en = [k for k in sorted(all_keys) if k not in TRANSLATIONS['English']]
missing_hi = [k for k in sorted(all_keys) if k not in TRANSLATIONS['Hindi']]
missing_mr = [k for k in sorted(all_keys) if k not in TRANSLATIONS['Marathi']]

print(f"Total unique translation keys across codebase: {len(all_keys)}")
print(f"Missing in English ({len(missing_en)}): {missing_en}")
print(f"Missing in Hindi ({len(missing_hi)}): {missing_hi}")
print(f"Missing in Marathi ({len(missing_mr)}): {missing_mr}")
