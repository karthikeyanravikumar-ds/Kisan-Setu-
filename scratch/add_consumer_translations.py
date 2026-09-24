# add_consumer_translations.py

with open('utils/translations.py', 'r', encoding='utf-8') as f:
    content = f.read()

en_keys = """              'consumer_hub_title': 'KISAN SETU · CONSUMER',
              'consumer_hub_sub': 'Fresh produce, directly connected to the farm.',
              'btn_order_produce': 'Order',
              'btn_order_now': 'Order Now',
              'confirm_consumer_order_title': 'CONFIRM ORDER',
              'confirm_consumer_order_sub': 'Review your order details before placing direct farm order.',
              'btn_confirm_order_now': 'Confirm Order',
              'consumer_order_success_title': 'ORDER PLACED',
              'consumer_order_success_desc': 'Your order has been placed directly with the farmer.',
              'btn_view_my_orders': 'View My Orders',
              'product_details_title': 'PRODUCT DETAILS',
              'no_product_photo': 'No product photo',
              'available_qty_label': 'Available Quantity',
              'farm_source_label': 'Farm / Location',
              'order_qty_prompt': 'Enter Quantity (kg)',
              'search_produce_placeholder': 'Search crop by name (e.g. Onion, Tomato)...',
              'sort_by_label': 'Sort by',
              'sort_price_low_high': 'Price: Low to High',
              'sort_price_high_low': 'Price: High to Low',
              'sort_qty_high_low': 'Quantity: High to Low',
              'all_grades_label': 'All Grades',
              'consumer_my_orders_title': 'MY ORDERS',
              'track_order_journey': 'Order Journey & Status',
              'zero_middleman_badge': '✓ Zero Intermediary Markup'}"""

hi_keys = """            'consumer_hub_title': 'किसान सेतु · उपभोक्ता',
            'consumer_hub_sub': 'ताज़ा कृषि उत्पाद, सीधे खेत से जुड़े हुए।',
            'btn_order_produce': 'ऑर्डर करें',
            'btn_order_now': 'अभी ऑर्डर करें',
            'confirm_consumer_order_title': 'ऑर्डर की पुष्टि करें',
            'confirm_consumer_order_sub': 'सीधा खेत से ऑर्डर करने से पहले अपनी ऑर्डर विवरण की समीक्षा करें।',
            'btn_confirm_order_now': 'ऑर्डर पक्का करें',
            'consumer_order_success_title': 'ऑर्डर सफलतापूर्वक दर्ज',
            'consumer_order_success_desc': 'आपका ऑर्डर सीधे किसान के पास दर्ज हो गया है।',
            'btn_view_my_orders': 'मेरी ऑर्डर्स देखें',
            'product_details_title': 'उत्पाद विवरण',
            'no_product_photo': 'कोई उत्पाद फोटो नहीं',
            'available_qty_label': 'उपलब्ध मात्रा',
            'farm_source_label': 'खेत / स्थान',
            'order_qty_prompt': 'मात्रा दर्ज करें (किग्रा)',
            'search_produce_placeholder': 'फसल खोजें (जैसे प्याज, टमाटर)...',
            'sort_by_label': 'क्रमबद्ध करें',
            'sort_price_low_high': 'मूल्य: कम से अधिक',
            'sort_price_high_low': 'मूल्य: अधिक से कम',
            'sort_qty_high_low': 'मात्रा: अधिक से कम',
            'all_grades_label': 'सभी ग्रेड',
            'consumer_my_orders_title': 'मेरी ऑर्डर्स',
            'track_order_journey': 'ऑर्डर यात्रा एवं स्थिति',
            'zero_middleman_badge': '✓ शून्य बिचौलिया शुल्क'}"""

mr_keys = """              'consumer_hub_title': 'किसान सेतू · ग्राहक',
              'consumer_hub_sub': 'ताजा शेतमाल, थेट शेतातून आपल्या दारी.',
              'btn_order_produce': 'ऑर्डर करा',
              'btn_order_now': 'आता ऑर्डर करा',
              'confirm_consumer_order_title': 'ऑर्डर निश्चित करा',
              'confirm_consumer_order_sub': 'थेट शेतातून ऑर्डर करण्यापूर्वी तपशील तपासा.',
              'btn_confirm_order_now': 'ऑर्डर निश्चित करा',
              'consumer_order_success_title': 'ऑर्डर यशस्वीरित्या नोंदवली',
              'consumer_order_success_desc': 'तुमची ऑर्डर थेट शेतकऱ्याकडे नोंदवली गेली आहे.',
              'btn_view_my_orders': 'माझ्या ऑर्डर्स पहा',
              'product_details_title': 'उत्पादन तपशील',
              'no_product_photo': 'उत्पादनाचा फोटो उपलब्ध नाही',
              'available_qty_label': 'उपलब्ध प्रमाण',
              'farm_source_label': 'शेत / ठिकाण',
              'order_qty_prompt': 'प्रमाण प्रविष्ट करा (किलो)',
              'search_produce_placeholder': 'पीक शोधा (उदा. कांदा, टोमॅटो)...',
              'sort_by_label': 'क्रमवारी',
              'sort_price_low_high': 'किंमत: कमी ते जास्त',
              'sort_price_high_low': 'किंमत: जास्त ते कमी',
              'sort_qty_high_low': 'प्रमाण: जास्त ते कमी',
              'all_grades_label': 'सर्व ग्रेड',
              'consumer_my_orders_title': 'माझ्या ऑर्डर्स',
              'track_order_journey': 'ऑर्डर प्रवास व स्थिती',
              'zero_middleman_badge': '✓ शून्य मध्यस्थ खर्च'}}"""

en_target = "'zero_middleman_badge': '✓ Zero Intermediary Markup'}"
hi_target = "'zero_middleman_badge': '✓ शून्य बिचौलिया शुल्क'}"
mr_target = "'zero_middleman_badge': '✓ शून्य मध्यस्थ खर्च'}}"

assert en_target in content, "EN target not found"
assert hi_target in content, "HI target not found"
assert mr_target in content, "MR target not found"

content = content.replace(en_target, en_keys).replace(hi_target, hi_keys).replace(mr_target, mr_keys)

with open('utils/translations.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully added Consumer translations!")
