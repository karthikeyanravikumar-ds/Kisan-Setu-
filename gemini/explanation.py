import time

from gemini.client import client


# Primary + fallback models
MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]


def explain_buyer_match(
    crop,
    quantity,
    quality,
    farmer_location,
    buyer_name,
    buyer_type,
    buyer_quantity,
    buyer_price,
    distance,
    match_score,
    language="English"
):

    prompt = f"""
You are an AI agricultural marketplace assistant.

Explain a buyer recommendation to a farmer in simple,
clear and trustworthy language.

IMPORTANT:
- Do not invent facts.
- Do not change any numbers.
- Do not guarantee profit.
- Do not guarantee price.
- Use only the information provided.
- Keep the explanation concise.
- Explain why this buyer was recommended.
- Respond entirely in {language}.
- Keep names, numbers and prices unchanged.

FARMER:
Crop: {crop}
Quantity: {quantity} kg
Quality: Grade {quality}
Location: {farmer_location}

BUYER:
Name: {buyer_name}
Type: {buyer_type}
Required Quantity: {buyer_quantity} kg
Maximum Price: ₹{buyer_price}/kg
Distance: {distance} km

MATCH SCORE:
{match_score}%

Give:
1. Recommended buyer
2. Match score
3. 3-4 simple reasons
4. A short caution to verify final price and quality.
"""

    last_error = None

    if client:
        # Try each available model
        for model in MODELS:
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=prompt
                    )
                    if response and response.text:
                        return response.text
                except Exception as e:
                    last_error = e
                    error_text = str(e)
                    if (
                        "503" in error_text
                        or "UNAVAILABLE" in error_text
                        or "high demand" in error_text.lower()
                        or "overloaded" in error_text.lower()
                    ):
                        if attempt == 0:
                            time.sleep(2)
                            continue
                    break

    # Rule-based fallback explanation (if offline, quota limit, or API unavailable)
    if language == "Marathi":
        return f"""
**शिफारस केलेले खरेदीदार:** {buyer_name} ({buyer_type})
**जुळवणी निर्देशांक (Setu Match):** {match_score}%

**मुख्य शिफारस कारणे:**
1. **उत्कृष्ट भाव:** खरेदीदाराचा कमाल दर ₹{buyer_price}/kg आहे, जो स्थानिक बाजारपेठेच्या तुलनेत अधिक नफा देतो.
2. **मागणी आणि पुरवठा संतुलन:** खरेदीदाराची आवश्यकता {buyer_quantity} kg असून आपल्या उपलब्ध {quantity} kg {crop} (Grade {quality}) साठ्याशी तंतोतंत जुळते.
3. **वाहतूक कार्यक्षमता:** अंतर {distance} km असून थेट महामार्ग कॉरिडॉरद्वारे जलद वाहतूक शक्य आहे.

*सावधानता: प्रत्यक्ष माल सुपूर्द करताना मालाची प्रत आणि अंतिम देयक अटी तपासा.*
"""
    elif language == "Hindi":
        return f"""
**अनुशंसित खरीदार:** {buyer_name} ({buyer_type})
**सेतु मैच स्कोर (Setu Match):** {match_score}%

**सिफारिश के मुख्य कारण:**
1. **आकर्षक मूल्य लाभ:** खरीदार ₹{buyer_price}/kg तक की पेशकश कर रहा है, जो स्थानीय मंडी से अधिक लाभ देता है।
2. **मांग और आपूर्ति संतुलन:** खरीदार की आवश्यकता {buyer_quantity} kg आपके उपलब्ध {quantity} kg {crop} (Grade {quality}) के सर्वथा अनुकूल है।
3. **सुलभ परिवहन:** दूरी मात्र {distance} km है और यह अनुकूलित राजमार्ग गलियारे पर स्थित है।

*सावधानी: कृपया माल सौंपते समय अंतिम गुणवत्ता, नमी और बिल की शर्तों की पुष्टि करें।*
"""
    else:
        return f"""
**Recommended Buyer:** {buyer_name} ({buyer_type})
**Setu AI Match Score:** {match_score}%

**Key Factors for Recommendation:**
1. **Price Realization:** The buyer offers up to ₹{buyer_price}/kg, providing an attractive margin above the mandi modal price.
2. **Volume & Grade Fit:** The required volume of {buyer_quantity} kg aligns with your available {quantity} kg of Grade {quality} {crop}.
3. **Route Proximity:** Located {distance} km away along an active, route-optimized delivery corridor.

*Caution: Please verify produce moisture, grade, and final invoice terms upon handover.*
"""