import pandas as pd


# =========================================================
# SCHEME RECOMMENDATION ENGINE
# =========================================================

def recommend_schemes(
    farmer,
    crop=None,
    purpose=None,
    top_n=5
):
    """
    Rule-based scheme relevance engine.

    This system identifies potentially relevant schemes.
    It does NOT make a final government eligibility decision.
    """

    schemes = pd.read_csv(
        "data/schemes.csv"
    )

    if schemes.empty:
        return pd.DataFrame()

    farmer_state = "Maharashtra"

    if crop is None:
        crop = farmer.get(
            "crop",
            "All"
        )

    crop = str(crop).strip()

    results = []

    for _, scheme in schemes.iterrows():

        score = 0
        reasons = []

        # -------------------------------------------------
        # STATE
        # -------------------------------------------------

        scheme_state = str(
            scheme["state"]
        ).strip()

        if (
            scheme_state.lower() == "all"
            or scheme_state.lower()
            == farmer_state.lower()
        ):

            score += 30

            reasons.append(
                "Available for Maharashtra"
            )

        # -------------------------------------------------
        # CROP
        # -------------------------------------------------

        scheme_crop = str(
            scheme["crop"]
        ).strip()

        if (
            scheme_crop.lower() == "all"
            or scheme_crop.lower()
            == crop.lower()
        ):

            score += 30

            reasons.append(
                f"Relevant to {crop}"
            )

        elif crop.lower() in [
            "onion",
            "tomato"
        ] and scheme_crop.lower() in [
            "vegetables",
            "all"
        ]:

            score += 25

            reasons.append(
                "Relevant to vegetable cultivation"
            )

        # -------------------------------------------------
        # FARM SIZE
        # -------------------------------------------------

        try:

            farm_size = float(
                farmer.get(
                    "farm_size_acres",
                    0
                )
            )

            if farm_size > 0:

                score += 10

                reasons.append(
                    "Farmer profile contains farm-size information"
                )

        except Exception:

            pass

        # -------------------------------------------------
        # PURPOSE
        # -------------------------------------------------

        if purpose:

            scheme_purpose = str(
                scheme["purpose"]
            ).lower()

            if purpose.lower() in scheme_purpose:

                score += 30

                reasons.append(
                    f"Matches purpose: {purpose}"
                )

        # -------------------------------------------------
        # RELEVANCE
        # -------------------------------------------------

        if score >= 60:

            relevance = "High"

        elif score >= 40:

            relevance = "Medium"

        else:

            relevance = "Low"

        if score > 0:

            results.append(
                {
                    "scheme_id": scheme["scheme_id"],
                    "scheme_name": scheme["scheme_name"],
                    "state": scheme.get("state", "All"),
                    "crop": scheme.get("crop", "All"),
                    "farmer_type": scheme.get("farmer_type", "All"),
                    "purpose": scheme["purpose"],
                    "relevance_score": score,
                    "relevance": relevance,
                    "reason": "; ".join(reasons),
                    "eligibility": scheme["eligibility"],
                    "benefit": scheme["benefit"],
                    "application_method": scheme[
                        "application_method"
                    ],
                    "official_source": scheme[
                        "official_source"
                    ]
                }
            )

    result_df = pd.DataFrame(results)

    if result_df.empty:
        return result_df

    result_df = (
        result_df
        .sort_values(
            "relevance_score",
            ascending=False
        )
        .head(top_n)
        .reset_index(drop=True)
    )

    return result_df