"""
Quality Intelligence Decision-Support Engine | Kisan Setu
Theme: 'Bharat, Reimagined'

Synthesizes farmer lot quality grades, buyer minimum quality requirements,
and optional preliminary AI quality observations.

Key Principles:
1. Purely factual comparison between farmer-entered grade and buyer requirement.
2. AI visual quality screening is strictly preliminary assistance — NOT certified grading.
3. AI quality observations NEVER silently overwrite stored farmer lot quality grades.
4. No automatic price adjustment or speculative quality claims.
"""

QUALITY_RANKS = {
    "A": 3,
    "B": 2,
    "C": 1,
}


def calculate_quality_intelligence(
    quality_grade,
    minimum_quality=None,
    crop=None,
    assessment=None
):
    """
    Evaluates produce quality grade against buyer requirement and packages
    preliminary AI quality observation context.

    Parameters:
        quality_grade (str or None): Farmer lot quality grade (e.g., 'A', 'B', 'C').
        minimum_quality (str or None, optional): Buyer minimum required quality grade.
        crop (str, optional): Target commodity/crop name.
        assessment (str or dict, optional): Optional preliminary AI quality screening output.

    Returns:
        dict: Structured quality intelligence decision support.
    """
    # ---------------------------------------------------------
    # 1. NORMALIZE QUALITY GRADE
    # ---------------------------------------------------------
    clean_grade = None
    if quality_grade is not None:
        raw_g = str(quality_grade).strip().upper()
        if raw_g:
            clean_grade = raw_g

    # ---------------------------------------------------------
    # 2. NORMALIZE REQUIRED MINIMUM QUALITY
    # ---------------------------------------------------------
    clean_required = None
    if minimum_quality is not None:
        raw_r = str(minimum_quality).strip().upper()
        if raw_r:
            clean_required = raw_r

    # ---------------------------------------------------------
    # 3. EVALUATE REQUIREMENT STATUS
    # ---------------------------------------------------------
    quality_requirement_met = None
    quality_status = "Requirement unavailable"

    if clean_grade is not None and clean_required is not None:
        farmer_rank = QUALITY_RANKS.get(clean_grade)
        buyer_rank = QUALITY_RANKS.get(clean_required)

        if farmer_rank is not None and buyer_rank is not None:
            if farmer_rank >= buyer_rank:
                quality_requirement_met = True
                quality_status = "Requirement met"
            else:
                quality_requirement_met = False
                quality_status = "Requirement not met"
        else:
            # Direct string equality fallback if non-standard grade format
            if clean_grade == clean_required:
                quality_requirement_met = True
                quality_status = "Requirement met"
            else:
                quality_requirement_met = False
                quality_status = "Requirement not met"
    else:
        quality_requirement_met = None
        quality_status = "Requirement unavailable"

    # ---------------------------------------------------------
    # 4. PARSE OPTIONAL AI QUALITY OBSERVATION
    # ---------------------------------------------------------
    assessment_available = False
    assessment_text = None
    assessment_source = "None"

    if assessment is not None:
        if isinstance(assessment, dict):
            res_str = str(assessment.get("result", "")).strip()
            if res_str:
                assessment_available = True
                assessment_text = res_str
                assessment_source = str(assessment.get("source", "Gemini AI"))
        elif isinstance(assessment, str):
            res_str = assessment.strip()
            if res_str:
                assessment_available = True
                assessment_text = res_str
                assessment_source = "AI Quality Assistance"

    # ---------------------------------------------------------
    # 5. CONSTRUCT FACTUAL EXPLANATION
    # ---------------------------------------------------------
    crop_str = f" for {crop}" if crop else ""
    if quality_status == "Requirement met":
        explanation = f"Farmer lot Grade {clean_grade}{crop_str} meets the buyer's minimum requirement of Grade {clean_required}."
    elif quality_status == "Requirement not met":
        explanation = f"Farmer lot Grade {clean_grade}{crop_str} does not meet the buyer's minimum requirement of Grade {clean_required}."
    elif clean_grade is not None:
        explanation = f"Farmer lot is classified as Grade {clean_grade}{crop_str}. Buyer quality requirement is not specified."
    else:
        explanation = f"Quality grade details are unavailable{crop_str}."

    # ---------------------------------------------------------
    # 6. STRUCTURED OUTPUT
    # ---------------------------------------------------------
    return {
        "crop": crop,
        "quality_grade": clean_grade,
        "required_quality": clean_required,
        "quality_requirement_met": quality_requirement_met,
        "quality_status": quality_status,
        "assessment_available": assessment_available,
        "assessment_text": assessment_text,
        "assessment_source": assessment_source,
        "disclaimer": "Preliminary AI-assisted observation — not certification.",
        "explanation": explanation,
    }
