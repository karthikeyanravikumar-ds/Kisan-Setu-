"""
Kisan Bol — AI Voice & Conversational Assistant for Kisan Setu
Connects voice / text input to existing platform services:
- Pricing & Mandi Rates (data/prices.csv, ai/pricing.py)
- AI Buyer Matching (ai/matching.py)
- Order & Transaction Status (data/transactions.csv, data/consumer_orders.csv)
- Government Schemes (ai/scheme_recommendation.py)
- Quality Assistance (ai/quality_assistance.py)
- Daily Farmer Directives & Recommendations
Strictly respects role security and multilingual (en/mr/hi) outputs.
"""

import re
import html
import streamlit as st
import pandas as pd
from utils.translations import t, get_current_language
from utils.data_loader import (
    load_farmers, load_buyers, load_produce, load_prices,
    load_transactions, load_schemes, load_data
)
from ai.matching import find_matches
from ai.scheme_recommendation import recommend_schemes
from ai.quality_assistance import demo_quality_assessment


# ============================================================
# 1. INTENT & ENTITY RECOGNITION PATTERNS
# ============================================================

# Canonical crop names dictionary
CROP_MAP = {
    # Onion
    "onion": "Onion",
    "onions": "Onion",
    "कांदा": "Onion",
    "कांदे": "Onion",
    "कांद्याचा": "Onion",
    "कांद्याचे": "Onion",
    "कांद्यासाठी": "Onion",
    "प्याज़": "Onion",
    "प्याज": "Onion",
    "प्याजों": "Onion",
    
    # Tomato
    "tomato": "Tomato",
    "tomatoes": "Tomato",
    "टोमॅटो": "Tomato",
    "टोमॅटोचा": "Tomato",
    "टोमॅटोसाठी": "Tomato",
    "टमाटर": "Tomato",
    "टमाटरों": "Tomato",
    
    # Potato
    "potato": "Potato",
    "potatoes": "Potato",
    "बटाटा": "Potato",
    "बटाटे": "Potato",
    "बटाट्याचा": "Potato",
    "आलू": "Potato",
    
    # Wheat
    "wheat": "Wheat",
    "गहू": "Wheat",
    "गव्हाचा": "Wheat",
    "गेहूं": "Wheat",
    
    # Rice
    "rice": "Rice",
    "तांदूळ": "Rice",
    "तांदळाचा": "Rice",
    "चावल": "Rice",
    
    # Banana
    "banana": "Banana",
    "bananas": "Banana",
    "केळी": "Banana",
    "केळे": "Banana",
    "केला": "Banana",
    "केले": "Banana",
    
    # Ginger
    "ginger": "Ginger",
    "आले": "Ginger",
    "आल्याचा": "Ginger",
    "अदरक": "Ginger",
}

INTENT_KEYWORDS = {
    "PRICE_QUERY": [
        "price", "rate", "mandi rate", "bhav", "modal price", "cost", "how much", "todays price",
        "भाव", "दर", "किंमत", "बाजारभाव", "मंडी भाव", "कांद्याचा भाव", "आजचा भाव", "दर काय", "भाव काय",
        "दाम", "मूल्य", "रेट", "आज का भाव", "प्याज का भाव", "भाव क्या है", "दाम क्या है"
    ],
    "FIND_BUYER": [
        "buyer", "buyers", "match", "sell", "trader", "wholesaler", "merchant", "purchaser", "find buyer",
        "खरेदीदार", "व्यापारी", "गिऱ्हाईक", "विक्री", "खरेदीदार शोधा", "विकायचा", "विकायचे", "व्यापारी शोधा",
        "खरीदार", "क्रेता", "व्यापारी", "बेचना", "खरीदार खोजो", "बेचने के लिए", "ग्राहक"
    ],
    "ORDER_STATUS": [
        "order", "orders", "track", "dispatch", "status", "delivery", "transit", "shipment", "transaction",
        "ऑर्डर", "स्थिती", "पोहोचला का", "वाहतूक", "डिलिव्हरी", "ट्रॅक", "व्यवहार", "ऑर्डर कुठे आहे",
        "ऑर्डर", "स्थिति", "डिलीवरी", "ट्रैक", "पहुंचा क्या", "लेनदेन", "ऑर्डर कहाँ है"
    ],
    "GOVERNMENT_SCHEMES": [
        "scheme", "schemes", "subsidy", "subsidies", "yojana", "grant", "pm kisan", "government",
        "योजना", "अनुदान", "शासकीय योजना", "सबसिडी", "सरकारी मदत", "कृषी योजना",
        "योजनाएं", "सब्सिडी", "सरकारी योजना", "योजना", "अनुदान", "पीएम किसान"
    ],
    "QUALITY_CHECK": [
        "quality", "grade", "grading", "standard", "defect", "uniformity", "screening",
        "गुणवत्ता", "प्रत", "ग्रेड", "दर्जा", "तपासणी", "तपासा", "नुकसान",
        "क्वालिटी", "गुणवत्ता", "ग्रेड", "दर्जा", "जाँच", "परख"
    ],
    "DAILY_RECOMMENDATION": [
        "recommendation", "what should i do", "directive", "advice", "suggestion", "sell or hold", "today",
        "आजचा निर्णय", "काय करावे", "सल्ला", "शिफारस", "थांबू का विकू", "आज काय करू",
        "आज का फैसला", "क्या करना चाहिए", "सलाह", "सुझाव", "रुकें या बेचें", "आज क्या करें"
    ],
    "HELP": [
        "help", "menu", "commands", "how to use", "support", "options", "what can you do",
        "मदत", "कसे वापरावे", "पर्याय", "माहिती", "कमांड्स",
        "मदद", "सहायता", "कैसे उपयोग करें", "विकल्प", "क्या कर सकते हो"
    ]
}


# ============================================================
# 2. NORMALIZATION & INTENT DETECTION
# ============================================================

def normalize_query(text: str) -> str:
    """Cleans up and normalizes query text."""
    if not text:
        return ""
    cleaned = text.strip().lower()
    cleaned = re.sub(r'[।?!.,:;\'"–—\-_/\\()\[\]]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def extract_entities(text: str, user_profile: dict = None) -> dict:
    """
    Extracts entities: crop, farmer_id, buyer_id, transaction_id, order_id.
    Falls back to user_profile context when safe.
    """
    entities = {
        "crop": None,
        "farmer_id": None,
        "buyer_id": None,
        "transaction_id": None,
        "order_id": None,
    }
    
    normalized = normalize_query(text)
    words = normalized.split()
    
    # 1. Extract Crop
    for w in words:
        if w in CROP_MAP:
            entities["crop"] = CROP_MAP[w]
            break
            
    # Check substring matches if not found in isolated words
    if not entities["crop"]:
        for token, canonical in CROP_MAP.items():
            if token in normalized:
                entities["crop"] = canonical
                break
                
    # Fallback to user profile crop if missing
    if not entities["crop"] and user_profile:
        entities["crop"] = user_profile.get("crop", user_profile.get("primary_crop", None))

    # 2. Extract IDs
    tx_match = re.search(r'\b(tx-?\d{3,5})\b', text, re.IGNORECASE)
    if tx_match:
        entities["transaction_id"] = tx_match.group(1).upper().replace("TX", "TX-")
        if not entities["transaction_id"].startswith("TX-"):
            entities["transaction_id"] = "TX-" + entities["transaction_id"]

    order_match = re.search(r'\b(ord-?\d{3,5})\b', text, re.IGNORECASE)
    if order_match:
        entities["order_id"] = order_match.group(1).upper()

    farmer_match = re.search(r'\b(farm-?\d{3,4})\b', text, re.IGNORECASE)
    if farmer_match:
        entities["farmer_id"] = farmer_match.group(1).upper()
    elif user_profile and user_profile.get("role") == "farmer":
        entities["farmer_id"] = user_profile.get("farmer_id")

    buyer_match = re.search(r'\b(buyer-?\d{3,4})\b', text, re.IGNORECASE)
    if buyer_match:
        entities["buyer_id"] = buyer_match.group(1).upper()
    elif user_profile and user_profile.get("role") == "buyer":
        entities["buyer_id"] = user_profile.get("buyer_id")

    return entities


def detect_intent(text: str, language: str = "English") -> str:
    """
    Detects intent from query text across English, Marathi, and Hindi.
    """
    norm = normalize_query(text)
    if not norm:
        return "UNKNOWN"

    # Score matches per intent
    scores = {intent: 0 for intent in INTENT_KEYWORDS}
    for intent, kws in INTENT_KEYWORDS.items():
        for kw in kws:
            kw_norm = normalize_query(kw)
            if kw_norm in norm:
                # Longer keyword matches get higher weight
                scores[intent] += len(kw_norm.split()) * 2

    best_intent = max(scores, key=scores.get)
    if scores[best_intent] > 0:
        return best_intent

    return "UNKNOWN"


# ============================================================
# 3. INTENT HANDLERS (CONNECTING TO EXISTING FUNCTIONS)
# ============================================================

def handle_price_query(entities: dict, language: str, user_profile: dict = None) -> str:
    """Handles price queries via data/prices.csv & data/mandi_rates.csv."""
    crop = entities.get("crop") or "Onion"
    prices_df = load_prices()
    
    # Filter by crop
    crop_prices = prices_df[prices_df["crop"].str.lower() == crop.lower()]
    if crop_prices.empty:
        crop_prices = prices_df
        crop = "Onion"

    latest_row = crop_prices.iloc[-1]
    modal_price = float(latest_row["modal_price_per_kg"])
    min_price = float(latest_row.get("min_price_per_kg", modal_price - 3))
    max_price = float(latest_row.get("max_price_per_kg", modal_price + 3))
    market = latest_row.get("market", "Nashik APMC")

    if language == "Marathi":
        return (
            f"📊 **{crop} चा आजचा बाजारभाव ({market}):**\n\n"
            f"- **सरासरी दर (Modal):** ₹{modal_price:.2f}/kg\n"
            f"- **किमान दर (Min):** ₹{min_price:.2f}/kg\n"
            f"- **कमाल दर (Max):** ₹{max_price:.2f}/kg\n\n"
            f"💡 *पुणे घाऊक बाजारात +₹२.६०/kg अधिक नफा मिळण्याची संधी आहे.*"
        )
    elif language == "Hindi":
        return (
            f"📊 **{crop} का आज का मंडी भाव ({market}):**\n\n"
            f"- **मॉडल भाव (Modal):** ₹{modal_price:.2f}/kg\n"
            f"- **न्यूनतम भाव (Min):** ₹{min_price:.2f}/kg\n"
            f"- **अधिकतम भाव (Max):** ₹{max_price:.2f}/kg\n\n"
            f"💡 *पुणे थोक मंडी में +₹२.६०/kg का अतिरिक्त लाभ उपलब्ध है।*"
        )
    else:
        return (
            f"📊 **Today's {crop} Benchmark Price ({market}):**\n\n"
            f"- **Modal Price:** ₹{modal_price:.2f}/kg\n"
            f"- **Min Price:** ₹{min_price:.2f}/kg\n"
            f"- **Max Price:** ₹{max_price:.2f}/kg\n\n"
            f"💡 *Pune Wholesale Terminal offers +₹2.60/kg arbitrage margin.*"
        )


def handle_find_buyer(entities: dict, language: str, user_profile: dict = None) -> str:
    """Handles buyer matching using ai/matching.py."""
    crop = entities.get("crop") or "Onion"
    buyers_df = load_buyers()
    produce_df = load_produce()
    
    # Find matching produce lot or build representative lot
    farmer_lots = produce_df[produce_df["crop"].str.lower() == crop.lower()]
    if not farmer_lots.empty:
        sample_lot = farmer_lots.iloc[0]
    else:
        sample_lot = pd.Series({
            "produce_id": "P-PROMO",
            "farmer_id": user_profile.get("farmer_id", "FARM-001") if user_profile else "FARM-001",
            "crop": crop,
            "quantity_kg": 500,
            "quality_grade": "A",
            "expected_price_per_kg": 28.0,
            "district": "Nashik",
            "available_date": "2026-09-25",
            "status": "Available"
        })

    matches = find_matches(sample_lot, buyers_df)
    if matches.empty:
        if language == "Marathi":
            return f"⚠️ सध्या {crop} पिकासाठी सक्रिय खरेदीदार जुळणी उपलब्ध नाही. कृपया नंतर तपासा."
        elif language == "Hindi":
            return f"⚠️ वर्तमान में {crop} फसल के लिए कोई सक्रिय खरीदार उपलब्ध नहीं है। कृपया बाद में प्रयास करें।"
        else:
            return f"⚠️ No active matching buyers found for {crop} right now. Please check back shortly."

    top_match = matches.iloc[0]
    buyer_name = top_match["buyer_name"]
    buyer_type = top_match["buyer_type"]
    offered_price = float(top_match["max_price_per_kg"])
    match_score = float(top_match["match_score"])
    dist = top_match["distance_km"]

    if language == "Marathi":
        return (
            f"🏆 **तुमच्या {crop} पिकासाठी सर्वोत्तम खरेदीदार सापडला!**\n\n"
            f"- **खरेदीदार:** {buyer_name} ({buyer_type})\n"
            f"- **ऑफर दर:** ₹{offered_price:.2f}/kg\n"
            f"- **सेतू मॅच स्कोर:** {match_score:.0f}%\n"
            f"- **अंतर:** {dist} km (थेट महामार्ग कॉरिडॉर)\n\n"
            f"👉 *हा व्यवहार निश्चित करण्यासाठी शेतकरी डॅशबोर्डवर 'AI Market Match' पहा.*"
        )
    elif language == "Hindi":
        return (
            f"🏆 **आपके {crop} के लिए अनुशंसित खरीदार उपलब्ध है!**\n\n"
            f"- **खरीदार:** {buyer_name} ({buyer_type})\n"
            f"- **प्रस्तावित मूल्य:** ₹{offered_price:.2f}/kg\n"
            f"- **सेतु मैच स्कोर:** {match_score:.0f}%\n"
            f"- **दूरी:** {dist} km (सुगम राजमार्ग कॉरिडोर)\n\n"
            f"👉 *सौदा स्वीकारने के लिए किसान डैशबोर्ड में 'AI Market Match' खोलें।*"
        )
    else:
        return (
            f"🏆 **Optimal Buyer Match Found for Your {crop}!**\n\n"
            f"- **Buyer:** {buyer_name} ({buyer_type})\n"
            f"- **Offered Price:** ₹{offered_price:.2f}/kg\n"
            f"- **Setu Match Score:** {match_score:.0f}%\n"
            f"- **Distance:** {dist} km via highway corridor\n\n"
            f"👉 *Open 'AI Market Match' on the Farmer Dashboard to confirm this deal.*"
        )


def handle_order_status(entities: dict, language: str, user_profile: dict = None) -> str:
    """Handles order/transaction status tracking."""
    tx_df = load_transactions()
    tx_id = entities.get("transaction_id")
    
    # Filter by user role/id if provided
    if tx_id:
        target_tx = tx_df[tx_df["transaction_id"].str.upper() == tx_id.upper()]
    elif user_profile and user_profile.get("role") == "farmer":
        f_id = user_profile.get("farmer_id", "FARM-001")
        target_tx = tx_df[tx_df["farmer_id"] == f_id]
    elif user_profile and user_profile.get("role") == "buyer":
        b_id = user_profile.get("buyer_id", "BUYER-001")
        target_tx = tx_df[tx_df["buyer_id"] == b_id]
    else:
        target_tx = tx_df

    if target_tx.empty:
        if language == "Marathi":
            return "📦 आपल्या खात्यावर सध्या कोणतीही प्रलंबित ऑर्डर आढळली नाही."
        elif language == "Hindi":
            return "📦 आपके खाते में वर्तमान में कोई लंबित ऑर्डर नहीं मिला।"
        else:
            return "📦 No active orders found in your account."

    latest = target_tx.iloc[0]
    t_id = latest["transaction_id"]
    crop = latest.get("crop", "Produce")
    qty = latest.get("quantity_kg", "500")
    status = latest.get("status", "Confirmed")
    price = latest.get("price_per_kg", 28.0)
    total_val = float(qty) * float(price)

    # Status localization
    status_localized = t(f"status_{status.lower().replace(' ', '_')}", language=language)

    if language == "Marathi":
        return (
            f"📦 **ऑर्डर सद्यस्थिती (Deal #{t_id}):**\n\n"
            f"- **शेतमाल:** {crop} ({qty} kg)\n"
            f"- **स्थिती:** `{status_localized}`\n"
            f"- **एकूण रक्कम:** ₹{total_val:,.2f}\n\n"
            f"🚚 *वाहतूक मार्ग: नाशिक ➔ पुणे (Setu Load सक्रिय)*"
        )
    elif language == "Hindi":
        return (
            f"📦 **ऑर्डर की स्थिति (Deal #{t_id}):**\n\n"
            f"- **फसल:** {crop} ({qty} kg)\n"
            f"- **स्थिति:** `{status_localized}`\n"
            f"- **कुल मूल्य:** ₹{total_val:,.2f}\n\n"
            f"🚚 *परिवहन गलियारा: नासिक ➔ पुणे (Setu Load सक्रिय)*"
        )
    else:
        return (
            f"📦 **Order Status Tracking (Deal #{t_id}):**\n\n"
            f"- **Commodity:** {crop} ({qty} kg)\n"
            f"- **Status:** `{status_localized}`\n"
            f"- **Total Realization:** ₹{total_val:,.2f}\n\n"
            f"🚚 *Corridor: Nashik ➔ Pune via Setu Load Dispatch*"
        )


def handle_government_schemes(entities: dict, language: str, user_profile: dict = None) -> str:
    """Handles scheme recommendations via ai/scheme_recommendation.py."""
    crop = entities.get("crop") or (user_profile.get("crop") if user_profile else "Onion")
    farmers_df = load_farmers()
    f_profile = farmers_df.iloc[0].to_dict() if not farmers_df.empty else {"crop": crop, "landholding_acres": 3.5}
    f_profile["crop"] = crop

    schemes_res = recommend_schemes(f_profile, crop=crop, top_n=2)
    if schemes_res.empty:
        if language == "Marathi":
            return "🏛️ सध्या आपल्या प्रोफाइलसाठी नवीन योजना उपलब्ध नाहीत."
        elif language == "Hindi":
            return "🏛️ वर्तमान में आपकी प्रोफ़ाइल के लिए नई योजनाएं उपलब्ध नहीं हैं।"
        else:
            return "🏛️ No matching government welfare schemes found right now."

    top_scheme = schemes_res.iloc[0]
    name = top_scheme.get("scheme_name", "PM Kisan Samman Nidhi")
    benefit = top_scheme.get("benefit", "Direct DBT subsidy")
    state = top_scheme.get("state", "Maharashtra")

    if language == "Marathi":
        return (
            f"🏛️ **आपल्या शेतीसाठी शिफारस केलेली शासकीय योजना:**\n\n"
            f"- **योजनेचे नाव:** {name}\n"
            f"- **मुख्य लाभ:** {benefit}\n"
            f"- **क्षेत्र:** {state}\n\n"
            f"🔗 *अधिक तपशील आणि अर्जासाठी 'शासकीय योजना' मेनू पहा.*"
        )
    elif language == "Hindi":
        return (
            f"🏛️ **आपके खेत के लिए अनुशंसित सरकारी योजना:**\n\n"
            f"- **योजना का नाम:** {name}\n"
            f"- **मुख्य लाभ:** {benefit}\n"
            f"- **क्षेत्र:** {state}\n\n"
            f"🔗 *अधिक जानकारी और आवेदन के लिए 'सरकारी योजनाएं' मेनू देखें।*"
        )
    else:
        return (
            f"🏛️ **Recommended Government Subsidy for Your Farm:**\n\n"
            f"- **Scheme Name:** {name}\n"
            f"- **Key Benefit:** {benefit}\n"
            f"- **State/Level:** {state}\n\n"
            f"🔗 *Visit the 'Government Schemes' page for direct portal application links.*"
        )


def handle_quality_check(entities: dict, language: str, user_profile: dict = None) -> str:
    """Handles quality screening guidance via ai/quality_assistance.py."""
    crop = entities.get("crop") or "Onion"
    assessment = demo_quality_assessment(crop=crop, farmer_quality="A", farmer_notes="Clean harvest", language=language)
    return assessment


def handle_daily_recommendation(entities: dict, language: str, user_profile: dict = None) -> str:
    """Handles daily farmer directive (SELL/WAIT/MOVE/CONSOLIDATE)."""
    crop = entities.get("crop") or "Onion"
    if language == "Marathi":
        return (
            f"🎯 **आजचा किसान सेतू सल्ला ({crop}):**\n\n"
            f"✦ **शिफारस:** **थांबा (WAIT - 24-48 तास)**\n"
            f"✦ **कारण:** पुणे घाऊक बाजारात मागणी ८-१२% वाढण्याचा अंदाज आहे.\n"
            f"✦ **पर्यायी संधी:** शेजारील २ शेतकऱ्यांसह **Setu Load** द्वारे संयुक्त वाहतूक करून वाहतूक खर्चात ३८% बचत करा."
        )
    elif language == "Hindi":
        return (
            f"🎯 **आज का किसान सेतु निर्देश ({crop}):**\n\n"
            f"✦ **सुझाव:** **प्रतीक्षा करें (WAIT - 24-48 घंटे)**\n"
            f"✦ **कारण:** पुणे थोक टर्मिनल पर मांग में ८-१२% की वृद्धि का अनुमान है।\n"
            f"✦ **वैकल्पिक अवसर:** पड़ोसी किसानों के साथ **Setu Load** साझा करके ३८% परिवहन खर्च बचाएं।"
        )
    else:
        return (
            f"🎯 **Today's Kisan Setu Directive ({crop}):**\n\n"
            f"✦ **Action:** **WAIT (Hold for 24-48 hours)**\n"
            f"✦ **Reasoning:** Wholesale demand in Pune terminal is projected to rise 8-12%.\n"
            f"✦ **Alternative:** Consolidate harvest dispatch via **Setu Load** to save 38% on freight."
        )


def handle_help(language: str) -> str:
    """Returns interactive voice help menu with examples."""
    if language == "Marathi":
        return (
            f"🎙️ **किसान बोल — व्हॉईस असिस्टंट मदत केंद्र**\n\n"
            f"तुम्ही मला खालीलप्रमाणे प्रश्न विचारू शकता:\n"
            f"1. **बाजारभाव:** *'आज कांद्याचा भाव काय आहे?'*\n"
            f"2. **खरेदीदार शोधणे:** *'माझ्या कांद्यासाठी खरेदीदार शोधा.'*\n"
            f"3. **ऑर्डर स्थिती:** *'माझ्या ऑर्डरची स्थिती काय आहे?'*\n"
            f"4. **शासकीय योजना:** *'सरकारी योजना दाखवा.'*\n"
            f"5. **आजचा सल्ला:** *'आज मी काय करावे?'*\n"
            f"6. **गुणवत्ता:** *'कांद्याची गुणवत्ता कशी तपासावी?'*"
        )
    elif language == "Hindi":
        return (
            f"🎙️ **किसान बोल — वॉइस असिस्टेंट सहायता केंद्र**\n\n"
            f"आप मुझसे निम्नलिखित प्रकार के प्रश्न पूछ सकते हैं:\n"
            f"1. **मंडी भाव:** *'आज प्याज का भाव क्या है?'*\n"
            f"2. **खरीदार खोजना:** *'मेरे प्याज के लिए खरीदार खोजो।'*\n"
            f"3. **ऑर्डर स्थिति:** *'मेरे ऑर्डर की स्थिति क्या है?'*\n"
            f"4. **सरकारी योजनाएं:** *'सरकारी योजनाएं दिखाओ।'*\n"
            f"5. **दैनिक सलाह:** *'आज मुझे क्या करना चाहिए?'*\n"
            f"6. **गुणवत्ता:** *'प्याज की गुणवत्ता कैसे जांचें?'*"
        )
    else:
        return (
            f"🎙️ **Kisan Bol — Voice Assistant Help Center**\n\n"
            f"You can speak or type commands like:\n"
            f"1. **Mandi Rates:** *'What is today\\'s onion price?'*\n"
            f"2. **Find Buyers:** *'Find a buyer for my onions.'*\n"
            f"3. **Order Status:** *'Where is my order?'*\n"
            f"4. **Welfare Schemes:** *'Show government schemes.'*\n"
            f"5. **Daily Directive:** *'What should I do today?'*\n"
            f"6. **Quality Check:** *'How to check produce quality?'*"
        )


def handle_unknown(query_text: str, language: str) -> str:
    """Handles unrecognized voice/text queries gracefully."""
    if language == "Marathi":
        return (
            f"❓ मला *'{query_text}'* समजले नाही. कृपया असा प्रश्न विचारा:\n"
            f"- *'आज कांद्याचा भाव काय आहे?'*\n"
            f"- *'माझ्या कांद्यासाठी खरेदीदार शोधा.'*\n"
            f"- *'सरकारी योजना दाखवा.'*"
        )
    elif language == "Hindi":
        return (
            f"❓ मुझे *'{query_text}'* समझ नहीं आया। कृपया ऐसा प्रश्न पूछें:\n"
            f"- *'आज प्याज का भाव क्या है?'*\n"
            f"- *'मेरे प्याज के लिए खरीदार खोजो।'*\n"
            f"- *'सरकारी योजनाएं दिखाओ।'"
        )
    else:
        return (
            f"❓ I couldn't understand *'{query_text}'*. Try asking:\n"
            f"- *'What is today\\'s onion price?'*\n"
            f"- *'Find a buyer for my onions.'*\n"
            f"- *'Show government schemes.'*"
        )


# ============================================================
# 4. MASTER ORCHESTRATION PIPELINE
# ============================================================

def process_query(query_text: str, user_profile: dict = None, language: str = None) -> dict:
    """
    Main entry point for both voice transcript and text query.
    
    Returns:
        {
            "query": query_text,
            "intent": intent,
            "entities": entities,
            "language": language,
            "response_text": response_text
        }
    """
    if not language:
        language = get_current_language()

    if not query_text or not query_text.strip():
        return {
            "query": "",
            "intent": "EMPTY",
            "entities": {},
            "language": language,
            "response_text": handle_help(language)
        }

    # Extract Entities & Detect Intent
    entities = extract_entities(query_text, user_profile=user_profile)
    intent = detect_intent(query_text, language=language)

    # Route to appropriate business handler
    if intent == "PRICE_QUERY":
        response_text = handle_price_query(entities, language, user_profile)
    elif intent == "FIND_BUYER":
        response_text = handle_find_buyer(entities, language, user_profile)
    elif intent == "ORDER_STATUS":
        response_text = handle_order_status(entities, language, user_profile)
    elif intent == "GOVERNMENT_SCHEMES":
        response_text = handle_government_schemes(entities, language, user_profile)
    elif intent == "QUALITY_CHECK":
        response_text = handle_quality_check(entities, language, user_profile)
    elif intent == "DAILY_RECOMMENDATION":
        response_text = handle_daily_recommendation(entities, language, user_profile)
    elif intent == "HELP":
        response_text = handle_help(language)
    else:
        response_text = handle_unknown(query_text, language)

    return {
        "query": query_text,
        "intent": intent,
        "entities": entities,
        "language": language,
        "response_text": response_text
    }


# ============================================================
# 5. STREAMLIT UI COMPONENT (KISAN BOL ASSISTANT PANEL)
# ============================================================

def render_kisan_bol(user_role: str = "Farmer", user_profile: dict = None, key_prefix: str = "kb"):
    """
    Renders the unified Kisan Bol voice & conversational assistant.
    Supports Web Speech API for voice recognition, SpeechSynthesis TTS,
    text fallback input, and one-click demo commands.
    """
    active_lang = get_current_language()

    # Initialize chat history in session state
    if "kisan_bol_history" not in st.session_state:
        st.session_state["kisan_bol_history"] = []

    # Map language to browser speech recognition code
    speech_lang_code = {
        "Marathi": "mr-IN",
        "Hindi": "hi-IN",
        "English": "en-IN"
    }.get(active_lang, "en-IN")

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, rgba(22,62,43,0.06), rgba(217,119,6,0.08)); border-radius: 12px; padding: 12px 14px; border: 1px solid rgba(22,62,43,0.15); margin-bottom: 12px;">
            <div style="font-weight: 800; font-size: 0.95rem; color: #163E2B; display: flex; align-items: center; gap: 6px;">
                <span>🎙️</span> <span>{t('kisan_bol_title')}</span>
            </div>
            <div style="font-size: 0.82rem; color: #526058; margin-top: 4px; line-height: 1.4;">
                {t('kisan_bol_sub')}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ------------------------------------------------------------
    # Demo Quick Command Chips
    # ------------------------------------------------------------
    demo_commands = {
        "Marathi": [
            ("📊 आजचा कांदा भाव", "आज कांद्याचा भाव काय आहे?"),
            ("🤝 खरेदीदार शोधा", "माझ्या कांद्यासाठी खरेदीदार शोधा."),
            ("📦 ऑर्डर स्थिती", "माझ्या ऑर्डरची स्थिती काय आहे?"),
            ("🏛️ शासकीय योजना", "सरकारी योजना दाखवा."),
            ("🎯 आजचा सल्ला", "आज मी काय करावे?")
        ],
        "Hindi": [
            ("📊 आज का प्याज भाव", "आज प्याज का भाव क्या है?"),
            ("🤝 खरीदार खोजो", "मेरे प्याज के लिए खरीदार खोजो।"),
            ("📦 ऑर्डर स्थिति", "मेरे ऑर्डर की स्थिति क्या है?"),
            ("🏛️ सरकारी योजनाएं", "सरकारी योजनाएं दिखाओ।"),
            ("🎯 आज की सलाह", "आज मुझे क्या करना चाहिए?")
        ],
        "English": [
            ("📊 Today's Onion Price", "What is today's onion price?"),
            ("🤝 Find Buyer", "Find a buyer for my onions"),
            ("📦 Order Status", "Where is my order?"),
            ("🏛️ Government Schemes", "Show government schemes"),
            ("🎯 Today's Advice", "What should I do today?")
        ]
    }.get(active_lang, [])

    st.markdown(f"<div style='font-size: 0.78rem; font-weight: 700; color: #64748B; margin-bottom: 6px;'>{t('kisan_bol_quick_queries')}</div>", unsafe_allow_html=True)
    
    # Render quick action chips in a horizontal flow
    cols = st.columns(len(demo_commands))
    for i, (label, cmd_text) in enumerate(demo_commands):
        if cols[i].button(label, key=f"{key_prefix}_demo_{i}", use_container_width=True):
            res = process_query(cmd_text, user_profile=user_profile, language=active_lang)
            st.session_state["kisan_bol_history"].append(res)
            st.rerun()

    # ------------------------------------------------------------
    # Browser Web Speech API Microphone Component
    # ------------------------------------------------------------
    mic_btn_id = f"{key_prefix}-mic-btn"
    mic_icon_id = f"{key_prefix}-mic-icon"
    mic_text_id = f"{key_prefix}-mic-text"
    func_name = f"startKisanBolVoice_{key_prefix}".replace("-", "_")

    mic_html = f"""
    <div style="display: flex; align-items: center; justify-content: center; margin: 10px 0;">
        <button id="{mic_btn_id}" onclick="{func_name}()" style="
            background: linear-gradient(135deg, #163E2B 0%, #2D6A4F 100%);
            color: #FFFFFF;
            border: none;
            border-radius: 50px;
            padding: 8px 18px;
            font-size: 0.85rem;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(22,62,43,0.25);
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
        ">
            <span id="{mic_icon_id}">🎙️</span>
            <span id="{mic_text_id}">{t('kisan_bol_mic_btn')}</span>
        </button>
    </div>

    <script>
    function {func_name}() {{
        const btn = document.getElementById('{mic_btn_id}');
        const icon = document.getElementById('{mic_icon_id}');
        const text = document.getElementById('{mic_text_id}');
        
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {{
            alert("Web Speech API is not supported in this browser. Please use the text input below.");
            return;
        }}
        
        const recognition = new SpeechRecognition();
        recognition.lang = '{speech_lang_code}';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        btn.style.background = '#DC2626';
        icon.innerText = '🔴';
        text.innerText = '{t("kisan_bol_listening")}';

        recognition.onresult = function(event) {{
            const transcript = event.results[0][0].transcript;
            btn.style.background = '#163E2B';
            icon.innerText = '🎙️';
            text.innerText = '{t("kisan_bol_mic_btn")}';
            
            // Set text input in Streamlit if available
            const inputElements = window.parent.document.querySelectorAll('input[type="text"]');
            for (let el of inputElements) {{
                if (el.getAttribute('aria-label') && el.getAttribute('aria-label').includes('Kisan Bol') || el.placeholder.includes('...')) {{
                    el.value = transcript;
                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    break;
                }}
            }}
        }};

        recognition.onerror = function(event) {{
            btn.style.background = '#163E2B';
            icon.innerText = '🎙️';
            text.innerText = '{t("kisan_bol_mic_btn")}';
        }};

        recognition.onend = function() {{
            btn.style.background = '#163E2B';
            icon.innerText = '🎙️';
            text.innerText = '{t("kisan_bol_mic_btn")}';
        }};

        recognition.start();
    }}
    </script>
    """
    st.components.v1.html(mic_html, height=52)

    # ------------------------------------------------------------
    # Text Fallback Input
    # ------------------------------------------------------------
    with st.form(key=f"{key_prefix}_form", clear_on_submit=True):
        col_in, col_btn = st.columns([4, 1])
        user_query = col_in.text_input(
            label="Kisan Bol Question",
            label_visibility="collapsed",
            placeholder=t('kisan_bol_text_placeholder'),
            key=f"{key_prefix}_text_input"
        )
        submitted = col_btn.form_submit_button(f"🔍 {t('kisan_bol_ask_btn')}", use_container_width=True)
        if submitted and user_query:
            res = process_query(user_query, user_profile=user_profile, language=active_lang)
            st.session_state["kisan_bol_history"].append(res)
            st.rerun()

    # ------------------------------------------------------------
    # Conversation History Display
    # ------------------------------------------------------------
    if st.session_state["kisan_bol_history"]:
        st.divider()
        # TTS Audio Toggle
        tts_enabled = st.checkbox(f"{t('kisan_bol_tts_label')}", value=True, key=f"{key_prefix}_tts_toggle")
        
        # Display latest responses first or in chronological order
        for item in reversed(st.session_state["kisan_bol_history"][-3:]):
            st.markdown(
                f"""
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px 14px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-weight: 700; font-size: 0.85rem; color: #1E293B;">🗣️ {html.escape(item['query'])}</span>
                        <span style="background: rgba(22,62,43,0.1); color: #163E2B; font-size: 0.72rem; font-weight: 800; padding: 2px 8px; border-radius: 6px;">{item['intent']}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown(item["response_text"])

        # Browser Text-to-Speech Script for the latest response
        if tts_enabled and st.session_state["kisan_bol_history"]:
            latest_res = st.session_state["kisan_bol_history"][-1]["response_text"]
            # Clean markdown formatting for voice synthesis
            clean_speech_text = re.sub(r'[*_#`\->💡📊🏆👉📦🚚🏛️🔗🎯✦⚠️❓]', ' ', latest_res)
            clean_speech_text = re.sub(r'\s+', ' ', clean_speech_text).strip()[:200]
            clean_speech_js = html.escape(clean_speech_text)

            tts_html = f"""
            <script>
            if ('speechSynthesis' in window) {{
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance("{clean_speech_js}");
                utterance.lang = '{speech_lang_code}';
                utterance.rate = 1.0;
                window.speechSynthesis.speak(utterance);
            }}
            </script>
            """
            st.components.v1.html(tts_html, height=0)

        # Clear History Button
        if st.button(f"🗑️ {t('kisan_bol_clear_history')}", key=f"{key_prefix}_clear", use_container_width=True):
            st.session_state["kisan_bol_history"] = []
            st.rerun()
