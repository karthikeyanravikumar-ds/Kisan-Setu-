"""
SMS & Low-Tech Feature Phone Gateway | Kisan Setu
Theme: 'Bharat, Reimagined'
Ensures full market access for farmers without smartphones or continuous internet.
"""

import streamlit as st
import pandas as pd

from utils.data_loader import load_farmers
from utils.sms_service import (
    process_sms,
    send_sms,
    load_sms_messages,
)
from utils.translations import t, get_current_language
from ui.theme import inject_custom_theme
from ui.setu_components import (
    render_brand_header,
    render_bharat_market_pulse,
)

inject_custom_theme()

language = get_current_language()

farmers = load_farmers()

render_bharat_market_pulse()

# Brand Header with Logo
render_brand_header(
    title=f"{t('brand_sms_title')}",
    subtitle=t("brand_sms_sub"),
    badge=t("badge_gsm_active"),
)

st.divider()

# Selected Farmer
current_user_id = st.session_state.get("user_id", "F001")
farmer_options = farmers["farmer_id"].tolist()
default_idx = farmer_options.index(current_user_id) if current_user_id in farmer_options else 0

col_sel1, col_sel2 = st.columns([2, 1])

with col_sel1:
    selected_farmer_id = st.selectbox(
        t("select_active_farmer_gsm"),
        farmer_options,
        index=default_idx,
        format_func=lambda x: f"{x} · {farmers[farmers['farmer_id']==x].iloc[0]['name']} - Tel: {str(farmers[farmers['farmer_id']==x].iloc[0]['phone']).replace('.0','')}",
    )

farmer = farmers[farmers["farmer_id"] == selected_farmer_id].iloc[0]
phone = str(farmer["phone"]).replace(".0", "")

# Metrics
c1, c2, c3 = st.columns(3)
c1.metric(f"📱 {t('gsm_status_label')}", t("sms_service_active"), "99.9% Uptime")
c2.metric(f"🌐 {t('internet_needed_label')}", t("no_offline_sms"), "Feature Phone")
c3.metric(f"🗣️ {t('native_language_label')}", farmer["language"], f"Tel: +91 {phone}")

st.divider()

# SMS Simulator & Interactive Commands
st.subheader(f"💬 {t('interactive_sms_terminal_title')}")
st.caption(t("interactive_sms_terminal_caption"))

col_cmd, col_sim = st.columns([1.5, 2.5])

with col_cmd:
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-radius: 10px; padding: 14px;">
            <div style="font-size: 0.8rem; font-weight: 800; color: #183A2A; text-transform: uppercase; margin-bottom: 8px;">
                {t('avail_sms_keywords')}
            </div>
            <div style="font-size: 0.85rem; color: #18201B; line-height: 1.6;">
                <code>PRICE ONION</code> → {t('sms_kw_price_onion')}<br>
                <code>PRICE TOMATO</code> → {t('sms_kw_price_tomato')}<br>
                <code>BUYERS ONION</code> → {t('sms_kw_buyers_onion')}<br>
                <code>SCHEMES</code> → {t('sms_kw_schemes')}<br>
                <code>HELP</code> → {t('sms_kw_help')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    quick_cmd = st.selectbox(
        t("quick_cmd_template"),
        ["PRICE ONION", "PRICE TOMATO", "BUYERS ONION", "SCHEMES", "HELP"],
    )

with col_sim:
    sms_input = st.text_input(t("simulate_outgoing_sms"), value=quick_cmd)

    if st.button(f"📲 {t('btn_send_sms')} →", type="primary", use_container_width=True):
        if sms_input.strip():
            with st.spinner(t("processing_sms_spinner")):
                response_text = process_sms(phone=phone, message=sms_input.strip())
                st.success(f"✅ {t('gateway_response_sent')}")
                st.markdown(
                    f"""
                    <div style="background: #183A2A; color: #FFFDF8; border-radius: 12px; padding: 16px; font-family: monospace; font-size: 0.95rem; margin-top: 8px; box-shadow: 0 4px 12px rgba(24,58,42,0.15);">
                        {response_text}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

st.divider()

# Historical SMS Message Log
st.subheader(f"📜 {t('farmer_sms_tx_history')}")
try:
    sms_logs = load_sms_messages()
    if not sms_logs.empty:
        st.dataframe(sms_logs, use_container_width=True, hide_index=True)
    else:
        st.info(t("no_sms_logs"))
except Exception:
    st.info(t("no_sms_logs"))

st.caption(f"ℹ️ {t('sms_footer')}")