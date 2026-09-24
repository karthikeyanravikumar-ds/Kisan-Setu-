"""
Feedback & Trust Assurance | Kisan Setu
Theme: 'Bharat, Reimagined'
Builds institutional trust through peer reviews, quality ratings, and fulfilment verification.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date

from ui.theme import inject_custom_theme
from ui.setu_components import (
    render_brand_header,
    render_bharat_market_pulse,
    render_empty_state,
)
from utils.translations import t, get_current_language

inject_custom_theme()

language = get_current_language()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FEEDBACK_FILE = DATA_DIR / "feedback.csv"
FEEDBACK_COLUMNS = ["feedback_id", "user_type", "user_id", "transaction_id", "rating", "comment"]

def load_feedback():
    if not FEEDBACK_FILE.exists():
        return pd.DataFrame(columns=FEEDBACK_COLUMNS)
    df = pd.read_csv(FEEDBACK_FILE)
    for c in FEEDBACK_COLUMNS:
        if c not in df.columns:
            df[c] = None
    return df[FEEDBACK_COLUMNS]

def save_feedback(user_type, user_id, transaction_id, rating, comment):
    df = load_feedback()
    num_list = []
    for fid in df["feedback_id"].dropna().astype(str):
        try:
            num_list.append(int(fid.replace("FB", "")))
        except ValueError:
            pass
    next_id = f"FB{(max(num_list) + 1 if num_list else 1):03d}"

    new_row = {
        "feedback_id": next_id,
        "user_type": user_type,
        "user_id": user_id,
        "transaction_id": transaction_id,
        "rating": rating,
        "comment": comment,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(FEEDBACK_FILE, index=False)
    return True, t("feedback_recorded_msg")

render_bharat_market_pulse()

# Brand Header with Logo
render_brand_header(
    title=f"{t('brand_feedback_title')}",
    subtitle=t("brand_feedback_sub"),
    badge=t("badge_trust_assurance"),
)

st.divider()

current_user_id = st.session_state.get("user_id", "F001")
current_role = st.session_state.get("user_role", "Farmer")

# Submit Feedback Form
with st.container(border=True):
    st.subheader(f"📝 {t('submit_feedback_title')}")
    c1, c2 = st.columns(2)
    with c1:
        tx_id_input = st.text_input(t("tx_order_id_label"), value="T001")
        rating = st.slider(t("rating_slider_label"), min_value=1, max_value=5, value=5)
    with c2:
        comment = st.text_area(t("review_textarea_label"), placeholder=t("review_placeholder"))

    if st.button(f"⭐ {t('btn_submit_feedback')} →", type="primary", use_container_width=True):
        if not tx_id_input.strip():
            st.error(t("err_valid_tx_id"))
        else:
            success, msg = save_feedback(
                user_type=current_role,
                user_id=current_user_id,
                transaction_id=tx_id_input.strip(),
                rating=rating,
                comment=comment.strip(),
            )
            st.success(f"✅ {msg}")
            st.rerun()

st.divider()

# Feedback History
st.subheader(f"📜 {t('recent_community_ratings')}")
feedback_df = load_feedback()

if feedback_df.empty:
    render_empty_state(t("no_feedback_recorded_title"), t("no_feedback_recorded_desc"))
else:
    avg_rating = pd.to_numeric(feedback_df["rating"], errors="coerce").mean()
    st.metric(t("platform_avg_rating"), f"{avg_rating:.1f} / 5.0", f"{len(feedback_df)} {t('verified_reviews_count')}")
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    for _, fb in feedback_df.iloc[::-1].iterrows():
        with st.container(border=True):
            col_l, col_r = st.columns([3, 1])
            with col_l:
                stars = "★" * int(fb["rating"]) + "☆" * (5 - int(fb["rating"]))
                st.markdown(f"<span style='color:#E8B83D; font-size:1.1rem; font-weight:800;'>{stars}</span> <b>({fb['rating']} / 5)</b>", unsafe_allow_html=True)
                st.write(f"\"{fb['comment']}\"")
                st.caption(f"{t('reviewer_label')}: {fb['user_type']} ({fb['user_id']}) · {t('transaction_label')}: {fb['transaction_id']}")
            with col_r:
                st.markdown(f"<div style='text-align:right; font-size:0.75rem; color:#176536; font-weight:700;'>✓ {t('verified_trade_badge')}</div>", unsafe_allow_html=True)

st.caption(f"ℹ️ {t('feedback_footer')}")