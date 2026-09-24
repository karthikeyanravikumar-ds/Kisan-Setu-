import base64

from gemini.client import client


# Primary + fallback models
MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]


def analyze_produce_quality(
    image_bytes,
    crop,
    farmer_quality,
    farmer_notes="",
    language="English",
    mime_type="image/jpeg"
):
    """
    AI-assisted preliminary quality screening.

    Returns:
        {
            "success": True/False,
            "source": "Gemini AI" / "Demo Fallback",
            "result": "...",
            "error": "..."
        }

    IMPORTANT:
    This is NOT certified agricultural grading.
    Final quality requires physical inspection.
    """

    if not image_bytes:

        return {
            "success": False,
            "source": "None",
            "result": "",
            "error": "No image was provided."
        }

    language_instruction = {
        "English": "English",
        "Marathi": "Marathi",
        "Hindi": "Hindi"
    }.get(language, "English")

    prompt = f"""
You are an AI agricultural quality-assistance system.

Analyze the uploaded produce image and provide a
PRELIMINARY VISUAL QUALITY SCREENING.

This is NOT certified agricultural grading.

Do not claim certainty.
Do not invent information that cannot be observed.

CROP:
{crop}

FARMER-ENTERED QUALITY:
Grade {farmer_quality}

FARMER NOTES:
{farmer_notes}

OUTPUT LANGUAGE:
{language_instruction}

Assess only what is reasonably visible in the image.

Look for:

1. Visible external damage
2. Spots or discoloration
3. Apparent maturity
4. Apparent size and uniformity
5. Visible signs of spoilage or defects
6. Overall preliminary quality impression

Return:

PRELIMINARY QUALITY:
A / B / C / Unable to assess

VISIBLE OBSERVATIONS:
- observation 1
- observation 2
- observation 3

POSSIBLE CONCERNS:
- concern 1
- concern 2

RECOMMENDATION:
Short farmer-friendly recommendation.

IMPORTANT:
Clearly state that physical inspection may be required
for final quality grading.

Keep the answer concise and farmer-friendly.
"""

    if not client:
        return {
            "success": False,
            "source": "None",
            "result": "",
            "error": "Gemini client is not initialized or API key is missing."
        }

    last_error = ""
    for model_name in MODELS:
        try:
            from google.genai import types
            part = types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type or "image/jpeg"
            )
            response = client.models.generate_content(
                model=model_name,
                contents=[part, prompt]
            )

            if response and response.text:
                return {
                    "success": True,
                    "source": f"Gemini AI ({model_name})",
                    "result": response.text,
                    "error": ""
                }
        except Exception as e:
            last_error = str(e)
            continue

    return {
        "success": False,
        "source": "Gemini AI",
        "result": "",
        "error": last_error or "Gemini models were unavailable."
    }


# ============================================================
# DEMO / FALLBACK QUALITY ENGINE
# ============================================================

def demo_quality_assessment(
    crop,
    farmer_quality,
    farmer_notes="",
    language="English"
):
    """
    Demo fallback used when Gemini is unavailable.

    IMPORTANT:
    This does NOT analyze the image.

    It creates a clearly labelled prototype assessment
    using farmer-entered information.
    """

    grade = str(farmer_quality).upper().strip()

    if grade == "A":

        observations = [
            "Farmer-entered grade indicates good-quality produce.",
            "No major defects were reported in the farmer notes."
        ]

        concerns = [
            "Physical inspection is still required.",
            "Image-based confirmation was unavailable."
        ]

        recommendation = (
            f"The {crop} can be considered for premium buyer matching "
            "subject to physical quality verification."
        )

    elif grade == "B":

        observations = [
            "Farmer-entered grade indicates standard-quality produce.",
            "The produce may be suitable for regular retail or bulk buyers."
        ]

        concerns = [
            "Check for visible damage, discoloration and spoilage.",
            "Physical inspection is recommended before final grading."
        ]

        recommendation = (
            f"The {crop} can be matched with standard retail or bulk buyers "
            "after quality verification."
        )

    else:

        observations = [
            "Farmer-entered grade indicates lower-quality produce.",
            "The produce may require additional sorting or grading."
        ]

        concerns = [
            "Possible quality variation within the lot.",
            "Physical inspection and sorting are recommended."
        ]

        recommendation = (
            f"Consider sorting the {crop} and matching suitable portions "
            "with buyers accepting lower grades."
        )

    # --------------------------------------------------------
    # English
    # --------------------------------------------------------

    if language == "English":

        return f"""
**PRELIMINARY QUALITY:**
Grade {grade}

**VISIBLE / ENTERED OBSERVATIONS:**
- {observations[0]}
- {observations[1]}

**POSSIBLE CONCERNS:**
- {concerns[0]}
- {concerns[1]}

**RECOMMENDATION:**
{recommendation}

⚠️ **Demo/Fallback Analysis:** Gemini image analysis was
temporarily unavailable. This assessment is based on
farmer-entered information and does NOT represent actual
image analysis.

Final quality grading should be verified through physical inspection.
"""

    # --------------------------------------------------------
    # Marathi
    # --------------------------------------------------------

    if language == "Marathi":

        return f"""
**प्राथमिक गुणवत्ता:**
ग्रेड {grade}

**निरीक्षण / नोंदवलेली माहिती:**
- शेतकऱ्याने दिलेल्या माहितीनुसार उत्पादनाची गुणवत्ता चांगली आहे.
- अंतिम गुणवत्ता निश्चित करण्यासाठी प्रत्यक्ष तपासणी आवश्यक आहे.

**संभाव्य बाबी:**
- उत्पादनातील नुकसान, रंगातील बदल किंवा खराब झालेले भाग तपासा.
- प्रत्यक्ष गुणवत्ता तपासणी करण्याची शिफारस केली जाते.

**शिफारस:**
{crop} साठी योग्य खरेदीदाराशी जुळणी करण्यापूर्वी
गुणवत्तेची प्रत्यक्ष पडताळणी करावी.

⚠️ **डेमो / फॉलबॅक विश्लेषण:** Gemini प्रतिमा विश्लेषण
तात्पुरते उपलब्ध नसल्यामुळे हे मूल्यांकन शेतकऱ्याने
दिलेल्या माहितीनुसार तयार केले आहे. हे प्रतिमेचे वास्तविक
AI विश्लेषण नाही.

अंतिम गुणवत्ता प्रत्यक्ष तपासणीद्वारे निश्चित करावी.
"""

    # --------------------------------------------------------
    # Hindi
    # --------------------------------------------------------

    if language == "Hindi":

        return f"""
**प्रारंभिक गुणवत्ता:**
ग्रेड {grade}

**निरीक्षण / दर्ज की जानकारी:**
- किसान द्वारा दी गई जानकारी के अनुसार उत्पाद की गुणवत्ता दर्ज {grade} है।
- अंतिम गुणवत्ता की पुष्टि के लिए भौतिक निरीक्षण आवश्यक है।

**संभावित चिंताएँ:**
- नुकसान, रंग में बदलाव या खराब उत्पाद की जाँच करें।
- अंतिम ग्रेडिंग से पहले भौतिक निरीक्षण की सलाह दी जाती है।

**सिफारिश:**
{crop} को उपयुक्त खरीदार से जोड़ने से पहले
गुणवत्ता की पुष्टि की जानी चाहिए।

⚠️ **डेमो / फॉलबैक विश्लेषण:** Gemini इमेज विश्लेषण
अस्थायी रूप से उपलब्ध नहीं था। यह मूल्यांकन किसान द्वारा
दी गई जानकारी पर आधारित है और वास्तविक इमेज AI विश्लेषण नहीं है।

अंतिम गुणवत्ता भौतिक निरीक्षण द्वारा सत्यापित की जानी चाहिए।
"""

    return demo_quality_assessment(
        crop,
        farmer_quality,
        farmer_notes,
        "English"
    )