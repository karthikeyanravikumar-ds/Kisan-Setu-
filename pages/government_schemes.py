"""
Government Scheme Recommendation Engine | Kisan Setu
Theme: 'Bharat, Reimagined'
Empowering farmers with targeted agricultural subsidy and scheme eligibility.
"""

import streamlit as st
import pandas as pd

from utils.data_loader import load_farmers
from ai.scheme_recommendation import recommend_schemes
from utils.translations import t, get_current_language
from ui.theme import inject_custom_theme
from ui.setu_components import (
    render_brand_header,
    render_bharat_market_pulse,
    render_empty_state,
)

inject_custom_theme()

language = get_current_language()

farmers = load_farmers()

render_bharat_market_pulse()

# Brand Header with Logo
render_brand_header(
    title=f"{t('brand_schemes_title')}",
    subtitle=t("brand_schemes_sub"),
    badge=t("badge_schemes_hub"),
)

st.divider()

# Farmer Selector
current_user_id = st.session_state.get("user_id", "F001")
farmer_options = farmers["farmer_id"].tolist()
default_idx = farmer_options.index(current_user_id) if current_user_id in farmer_options else 0

col_sel1, col_sel2 = st.columns([2, 1])

with col_sel1:
    selected_farmer_id = st.selectbox(
        t("select_farmer_profile_label"),
        farmer_options,
        index=default_idx,
        format_func=lambda x: f"{x} · {farmers[farmers['farmer_id']==x].iloc[0]['name']} ({farmers[farmers['farmer_id']==x].iloc[0]['village']}, {farmers[farmers['farmer_id']==x].iloc[0]['district']})",
    )

farmer = farmers[farmers["farmer_id"] == selected_farmer_id].iloc[0]

# Profile Metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric(f"👨‍🌾 {t('farmer_name_input')}", farmer["name"])
c2.metric(f"🌱 {t('crop')}", farmer["crop"])
c3.metric(f"📐 {t('landholding_label')}", f"{farmer['farm_size_acres']} acres")
c4.metric(f"📍 {t('matrix_col_district')}", farmer["district"])

st.divider()

# Scheme Recommendations
st.subheader(f"📋 {t('recommended_schemes_title')}")
st.caption(t("recommended_schemes_caption"))

recommended = recommend_schemes(farmer=farmer.to_dict(), crop=farmer["crop"])

if recommended.empty:
    render_empty_state(t("no_matching_schemes_title"), t("no_matching_schemes_desc"))
else:
    for _, s in recommended.iterrows():
        with st.container(border=True):
            col_info, col_action = st.columns([3, 1])
            with col_info:
                st.markdown(f"### 🏛️ {s['scheme_name']}")
                st.markdown(
                    f"""
                    <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px;">
                        <span style="background: #E6F5EC; color: #176536; font-size: 0.75rem; font-weight: 700; padding: 2px 8px; border-radius: 4px;">{s.get('state', 'All')}</span>
                        <span style="background: #FAF7F0; border: 1px solid #E5DFD3; color: #68756C; font-size: 0.75rem; padding: 2px 8px; border-radius: 4px;">{t('crop')}: {s.get('crop', 'All')}</span>
                        <span style="background: #FAF7F0; border: 1px solid #E5DFD3; color: #68756C; font-size: 0.75rem; padding: 2px 8px; border-radius: 4px;">{t('category_label')}: {s.get('farmer_type', 'All')}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.write(f"**{t('key_benefit_label')}:** {s['benefit']}")
                st.write(f"**{t('eligibility_label')}:** {s['eligibility']}")
                st.caption(f"📝 {t('application_method_label')}: {s['application_method']}")

            with col_action:
                st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
                st.markdown(
                    f"""
                    <div style="background: #FFFDF8; border: 1px dashed #D4CBB8; border-radius: 8px; padding: 12px; text-align: center;">
                        <div style="font-size: 0.7rem; font-weight: 700; color: #68756C; text-transform: uppercase;">{t('official_portal_label')}</div>
                        <div style="font-size: 0.85rem; font-weight: 700; color: #183A2A; margin: 4px 0;">{s['official_source']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

st.caption(f"ℹ️ {t('schemes_footer')}")