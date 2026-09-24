# add_logistics_translations.py

with open('utils/translations.py', 'r', encoding='utf-8') as f:
    content = f.read()

en_keys = """              'logistics_hub_header': 'KISAN SETU · LOGISTICS HUB',
              'logistics_hub_subtitle': 'Coordinate farm-to-market deliveries.',
              'active_deliveries_label': 'Active Deliveries',
              'in_transit_label': 'In Transit',
              'delivered_label': 'Delivered',
              'fleet_vehicles_label': 'Fleet Capacity',
              'active_delivery_board_title': 'ACTIVE DELIVERY BOARD',
              'btn_view_delivery': 'View Delivery',
              'btn_hide_delivery': 'Hide Delivery',
              'delivery_detail_title': 'DELIVERY DETAILS',
              'origin_label': 'Origin / From',
              'destination_label': 'Destination / To',
              'estimated_travel_time': 'Estimated Travel Time',
              'vehicle_load_assigned': 'Vehicle / Load',
              'no_active_deliveries_title': 'NO ACTIVE DELIVERIES',
              'no_active_deliveries_desc': 'No deliveries currently require logistics attention.',
              'btn_dispatch_start': 'Dispatch / Start Transit',
              'btn_mark_delivered_logistics': 'Mark Delivered',
              'btn_complete_settle': 'Complete & Settle',
              'logistics_summary_title': 'LOGISTICS SUMMARY',
              'zero_middleman_badge': '✓ Zero Intermediary Markup'}"""

hi_keys = """            'logistics_hub_header': 'किसान सेतु · परिवहन हब',
            'logistics_hub_subtitle': 'खेत से बाजार तक कृषि परिवहन का समन्वय करें।',
            'active_deliveries_label': 'सक्रिय डिलीवरी',
            'in_transit_label': 'रास्ते में',
            'delivered_label': 'वितरित',
            'fleet_vehicles_label': 'फ्लीट क्षमता',
            'active_delivery_board_title': 'सक्रिय डिलीवरी बोर्ड',
            'btn_view_delivery': 'डिलीवरी देखें',
            'btn_hide_delivery': 'डिलीवरी छुपाएं',
            'delivery_detail_title': 'डिलीवरी विवरण',
            'origin_label': 'प्रारंभिक स्थान / से',
            'destination_label': 'गंतव्य स्थान / तक',
            'estimated_travel_time': 'अनुमानित यात्रा समय',
            'vehicle_load_assigned': 'वाहन / भार',
            'no_active_deliveries_title': 'कोई सक्रिय डिलीवरी नहीं',
            'no_active_deliveries_desc': 'वर्तमान में किसी डिलीवरी पर कार्रवाई की आवश्यकता नहीं है।',
            'btn_dispatch_start': 'वाहन रवाना करें',
            'btn_mark_delivered_logistics': 'वितरित चिह्नित करें',
            'btn_complete_settle': 'पूर्ण एवं निपटान करें',
            'logistics_summary_title': 'परिवहन सारांश',
            'zero_middleman_badge': '✓ शून्य बिचौलिया शुल्क'}"""

mr_keys = """              'logistics_hub_header': 'किसान सेतू · वाहतूक हब',
              'logistics_hub_subtitle': 'शेतातून बाजारापर्यंत शेतमाल वाहतुकीचे व्यवस्थापन करा.',
              'active_deliveries_label': 'सक्रिय डिलिव्हरी',
              'in_transit_label': 'मार्गावर',
              'delivered_label': 'पोहोचवले',
              'fleet_vehicles_label': 'फ्लीट क्षमता',
              'active_delivery_board_title': 'सक्रिय डिलिव्हरी फलक',
              'btn_view_delivery': 'डिलिव्हरी पहा',
              'btn_hide_delivery': 'डिलिव्हरी लपवा',
              'delivery_detail_title': 'डिलिव्हरी तपशील',
              'origin_label': 'सुरुवातीचे ठिकाण / येथून',
              'destination_label': 'अंतिम ठिकाण / येथे',
              'estimated_travel_time': 'अंदाजे प्रवासाची वेळ',
              'vehicle_load_assigned': 'वाहन / लोड',
              'no_active_deliveries_title': 'कोणतीही सक्रिय डिलिव्हरी नाही',
              'no_active_deliveries_desc': 'सध्या कोणत्याही डिलिव्हरीवर कारवाईची आवश्यकता नाही.',
              'btn_dispatch_start': 'वाहन रवाना करा',
              'btn_mark_delivered_logistics': 'पोहोचवले म्हणून नोंदवा',
              'btn_complete_settle': 'पूर्ण व व्यवहार पूर्ण करा',
              'logistics_summary_title': 'वाहतूक सारांश',
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

print("Successfully added Logistics translations!")
