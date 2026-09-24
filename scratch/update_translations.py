# update_translations.py

with open('utils/translations.py', 'r', encoding='utf-8') as f:
    content = f.read()

en_target = "'zero_middleman_badge': '\u2713 Zero Intermediary Markup'}"
en_replace = (
    "'kisan_bol_caption': 'Multilingual Voice & Chat AI Advisory',\n"
    "              'for_total_qty': 'for total volume',\n"
    "              'spread_disclaimer': 'Potential spread based on real-time market data; final realization subject to fulfillment.',\n"
    "              'zero_middleman_badge': '\u2713 Zero Intermediary Markup'}"
)

hi_target = "'zero_middleman_badge': '\u2713 \u0936\u0942\u0928\u094d\u092f \u092c\u093f\u091a\u094c\u0932\u093f\u092f\u093e \u0936\u0941\u0932\u094d\u0915'}"
hi_replace = (
    "'kisan_bol_caption': '\u092c\u0939\u0941\u092d\u093e\u0937\u0940 \u0906\u0935\u093e\u091c \u0914\u0930 \u091a\u0948\u091f \u090f\u0906\u0908 \u0938\u0932\u093e\u0939\u0915\u093e\u0930',\n"
    "            'for_total_qty': '\u0915\u0941\u0932 \u092e\u093e\u0924\u094d\u0930\u093e \u0915\u0947 \u0932\u093f\u090f',\n"
    "            'spread_disclaimer': '\u0938\u0902\u092d\u093e\u0935\u093f\u0924 \u0905\u0902\u0924\u0930 \u0935\u093e\u0938\u094d\u0924\u0935\u093f\u0915 \u0938\u092e\u092f \u0915\u0947 \u092c\u093e\u091c\u093e\u0930 \u0921\u0947\u091f\u093e \u092a\u0930 \u0906\u0927\u093e\u0930\u093f\u0924 \u0939\u0948; \u0905\u0902\u0924\u093f\u092e \u092a\u094d\u0930\u093e\u092a\u094d\u0924\u093f \u0935\u093f\u0924\u0930\u0923 \u092a\u0930 \u0928\u093f\u0930\u094d\u092d\u0930 \u0915\u0930\u0924\u0940 \u0939\u0948\u0964',\n"
    "            'zero_middleman_badge': '\u2713 \u0936\u0942\u0928\u094d\u092f \u092c\u093f\u091a\u094c\u0932\u093f\u092f\u093e \u0936\u0941\u0932\u094d\u0915'}"
)

mr_target = "'zero_middleman_badge': '\u2713 \u0936\u0942\u0928\u094d\u092f \u092e\u0927\u094d\u092f\u0938\u094d\u0925 \u0916\u0930\u094d\u091a'}}"
mr_replace = (
    "'kisan_bol_caption': '\u092c\u0939\u0941\u092d\u093e\u0937\u093f\u0915 \u0935\u094d\u0939\u0949\u0907\u0938 \u0906\u0923\u093f \u091a\u0945\u091f \u090f\u0906\u092f \u0938\u0932\u094d\u0932\u093e\u0917\u093e\u0930',\n"
    "              'for_total_qty': '\u090f\u0915\u0942\u0923 \u092a\u0930\u093f\u092e\u093e\u0923\u093e\u0938\u093e\u0920\u0940',\n"
    "              'spread_disclaimer': '\u0938\u0902\u092d\u093e\u0935\u094d\u092f \u092b\u0930\u0915 \u0925\u0947\u091f \u092c\u093e\u091c\u093e\u0930 \u092e\u093e\u0939\u093f\u0924\u0940\u0935\u0930 \u0906\u0927\u093e\u0930\u093f\u0924 \u0906\u0939\u0947; \u0905\u0902\u0924\u093f\u092e \u092a\u094d\u0930\u093e\u092a\u094d\u0924\u0940 \u092a\u094d\u0930\u0924\u094d\u092f\u0915\u094d\u0937 \u0935\u093f\u0924\u0930\u0923\u093e\u0935\u0930 \u0905\u0935\u0932\u0902\u092c\u0942\u0928 \u0905\u0938\u0947\u0932.',\n"
    "              'factor_demand': '\u0909\u091a\u094d\u091a \u0938\u094d\u0925\u093e\u0928\u093f\u0915 \u0906\u0923\u093f \u0938\u0902\u0938\u094d\u0925\u093e\u0924\u094d\u092e\u0915 \u092e\u093e\u0917\u0923\u0940',\n"
    "              'factor_distance': '\u0925\u0947\u091f \u0935\u093e\u0939\u0924\u0942\u0915 \u092e\u093e\u0930\u094d\u0917 \u0906\u0923\u093f \u0915\u093e\u0930\u094d\u092f\u0915\u094d\u0937\u092e \u0935\u094d\u092f\u0935\u0938\u094d\u0925\u093e',\n"
    "              'factor_qty_compat': '\u092a\u094d\u0930\u092e\u093e\u0923 \u0905\u0924\u093f\u0936\u092f \u092f\u094b\u0917\u094d\u092f',\n"
    "              'factor_quality_compat': '\u092a\u094d\u0930\u0924\u0935\u093e\u0930\u0940 / \u0917\u0941\u0923\u0935\u0924\u094d\u0924\u093e \u091c\u0941\u0933\u0935\u0923\u0940',\n"
    "              'zero_middleman_badge': '\u2713 \u0936\u0942\u0928\u094d\u092f \u092e\u0927\u094d\u092f\u0938\u094d\u0925 \u0916\u0930\u094d\u091a'}}"
)

assert en_target in content, "EN target not found"
assert hi_target in content, "HI target not found"
assert mr_target in content, "MR target not found"

content = content.replace(en_target, en_replace).replace(hi_target, hi_replace).replace(mr_target, mr_replace)

with open('utils/translations.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully updated translations.py")
