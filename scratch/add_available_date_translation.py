# add_available_date_translation.py

with open('utils/translations.py', 'r', encoding='utf-8') as f:
    content = f.read()

en_target = "'available_matches_label': 'Available Matches',"
en_replace = "'available_matches_label': 'Available Matches',\n              'available_date': 'Available Date',"

hi_target = "'available_matches_label': 'उपलब्ध मिलान',"
hi_replace = "'available_matches_label': 'उपलब्ध मिलान',\n            'available_date': 'उपलब्धता तिथि',"

mr_target = "'available_matches_label': 'उपलब्ध जुळवण्या',"
mr_replace = "'available_matches_label': 'उपलब्ध जुळवण्या',\n              'available_date': 'उपलब्धता दिनांक',"

assert en_target in content, "EN target not found"
assert hi_target in content, "HI target not found"
assert mr_target in content, "MR target not found"

content = content.replace(en_target, en_replace).replace(hi_target, hi_replace).replace(mr_target, mr_replace)

with open('utils/translations.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully added available_date translations!")
