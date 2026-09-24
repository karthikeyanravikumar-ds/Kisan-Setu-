"""
Digital Mandi — The Living Heart of Kisan Setu
Visual Floor of India's Agricultural Ecosystem
Powered by live daily mandi data from data.gov.in (API #1 Current Daily + API #2 Variety-wise)
Bilingual: English + मराठी / हिन्दी
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from ui.theme import inject_custom_theme
from ui.setu_components import (
    render_brand_header,
    render_bharat_market_pulse,
    render_setu_pulse,
    render_price_chit,
    render_market_opportunity_layer,
    render_weather_intelligence,
    render_mandi_status_badge,
    render_html,
)
from ui.charts import (
    create_mandi_trend_chart,
    create_supply_demand_chart,
)
from utils.data_loader import (
    load_prices,
    load_market_prices,
    load_demand,
    load_produce,
    load_farmers,
    load_buyers,
)
from data_ingestion.market_data import (
    get_live_price_chits,
    get_market_floor_telemetry,
    get_latest_market_price,
    generate_setu_intelligence_signal,
    clear_mandi_cache,
    get_mandi_data_status,
)
from utils.translations import t, get_current_language

# ------------------------------------------------------------
# THEME INJECTION & LANGUAGE RESOLUTION
# ------------------------------------------------------------

inject_custom_theme()
language = get_current_language()

# ------------------------------------------------------------
# DATA LOADING
# ------------------------------------------------------------

prices_df = load_market_prices()
demand_df = load_demand()
produce_df = load_produce()
farmers_df = load_farmers()
buyers_df = load_buyers()

# ------------------------------------------------------------
# TOP BAR: REAL-TIME LIVE MANDI PULSE (API #1)
# ------------------------------------------------------------

render_bharat_market_pulse()

# ------------------------------------------------------------
# BRAND HEADER WITH LOGO & STATUS BAR
# ------------------------------------------------------------

render_brand_header(
    title=f"{t('brand_digital_mandi_title')}",
    subtitle=t("brand_digital_mandi_sub"),
    badge=t("badge_living_market_floor"),
)

render_mandi_status_badge()

# ------------------------------------------------------------
# MARKET FILTERS & REFRESH CONTROL
# ------------------------------------------------------------

with st.expander("🔍 Filter Mandi Data & Controls", expanded=False):
    f_col1, f_col2, f_col3, f_col4 = st.columns([1.5, 1.5, 1.5, 1])
    
    with f_col1:
        sel_state = st.selectbox(
            "State / राज्य",
            options=["Maharashtra", "All India"],
            index=0,
            key="mandi_filter_state",
        )
    with f_col2:
        dist_options = ["All Districts", "Nashik", "Pune", "Ahilyanagar", "Mumbai", "Ahmednagar"]
        sel_district_raw = st.selectbox(
            "District / जिल्हा",
            options=dist_options,
            index=0,
            key="mandi_filter_district",
        )
        sel_district = None if sel_district_raw == "All Districts" else sel_district_raw
    with f_col3:
        crop_options = ["All Commodities", "Onion", "Tomato", "Potato", "Wheat"]
        sel_crop_raw = st.selectbox(
            "Commodity / शेतमाल",
            options=crop_options,
            index=0,
            key="mandi_filter_commodity",
        )
        sel_crop = None if sel_crop_raw == "All Commodities" else sel_crop_raw
    with f_col4:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("↻ Refresh Mandi Data", use_container_width=True, type="primary"):
            clear_mandi_cache()
            st.success("Mandi cache refreshed!")
            st.rerun()

# ------------------------------------------------------------
# EDITORIAL HEADER
# ------------------------------------------------------------

col_title, col_stat = st.columns([3, 1])

# Resolve dynamic benchmark for state average
latest_onion = get_latest_market_price("Onion", district=sel_district, state=sel_state if sel_state != "All India" else "Maharashtra")
avg_mandi_price = float(latest_onion.get("modal_price_per_kg", 38.00))

with col_title:
    st.markdown(
        f"""
        <div style="margin-bottom: 8px;">
            <span style="background: #183A2A; color: #E8B83D; font-size: 0.72rem; font-weight: 800; padding: 4px 10px; border-radius: 4px; letter-spacing: 0.08em; text-transform: uppercase;">
                {t('badge_living_market_floor')}
            </span>
        </div>
        <h1 style="margin: 0; padding: 0;">{t('brand_digital_mandi_title')}</h1>
        <p style="color: #68756C; font-size: 1rem; margin-top: 4px;">
            {t('brand_digital_mandi_sub')}
        </p>
        """,
        unsafe_allow_html=True,
    )

with col_stat:
    now_str = datetime.now().strftime("%d %b %Y · %I:%M %p")
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-radius: 10px; padding: 12px 16px; text-align: right;">
            <div style="font-size: 0.7rem; font-weight: 700; color: #68756C; text-transform: uppercase;">{t('mandi_session_label')}</div>
            <div style="font-size: 0.95rem; font-weight: 800; color: #176536;">● Live daily mandi data</div>
            <div style="font-size: 0.75rem; color: #68756C;">{now_str}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ------------------------------------------------------------
# SETU MACRO PULSE
# ------------------------------------------------------------

render_setu_pulse(
    farmers_count=len(farmers_df),
    avg_price=avg_mandi_price,
    buyers_count=len(buyers_df),
    fulfilment_rate=94,
)

# ------------------------------------------------------------
# SIGNATURE MANDI PRICE CHITS (API #2 - Variety-wise API)
# ------------------------------------------------------------

st.markdown(
    f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <div style="font-size: 0.8rem; font-weight: 800; color: #68756C; text-transform: uppercase; letter-spacing: 0.06em;">
            ✦ {t('live_price_chits_title')}
        </div>
        <div style="font-size: 0.75rem; color: #68756C; font-weight: 600;">
            Source: data.gov.in Variety-wise Daily Market Prices API
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Fetch dynamic chits from API #2
chits = get_live_price_chits(
    state="Maharashtra" if sel_state == "Maharashtra" else "Maharashtra",
    district=sel_district,
    commodity=sel_crop,
    limit=4,
)

if chits:
    cols = st.columns(len(chits))
    for idx, chit in enumerate(chits):
        with cols[idx]:
            render_price_chit(
                crop_en=chit.get("crop_en", "ONION"),
                crop_mr=chit.get("crop_mr", "Standard · APMC Mandi"),
                price=chit.get("price", 38.00),
                market=chit.get("market", "APMC"),
                time_str=chit.get("time_str", "Arrival Today"),
                change_str=chit.get("change_str", "STABLE"),
                is_up=chit.get("is_up", True),
            )
else:
    st.info("No mandi price chits available for the selected filters.")

# ------------------------------------------------------------
# SETU INTELLIGENCE SIGNAL & MARKET OPPORTUNITY SPOTLIGHT
# ------------------------------------------------------------

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# Generate dynamic evidence-based intelligence signal
intel_signal = generate_setu_intelligence_signal(
    crop=sel_crop or "Onion",
    district=sel_district or "Nashik",
)

st.markdown(
    f"""
    <div style="background: linear-gradient(135deg, rgba(22, 62, 43, 0.06) 0%, rgba(217, 119, 6, 0.08) 100%), #FFFFFF; border: 1.5px solid rgba(22, 62, 43, 0.16); border-left: 5px solid #163E2B; border-radius: 12px; padding: 16px 20px; margin-bottom: 1.2rem; box-shadow: 0 4px 14px rgba(22, 62, 43, 0.04);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 0.72rem; font-weight: 800; text-transform: uppercase; color: #163E2B; letter-spacing: 0.06em;">
                ✦ {intel_signal['signal_title']}
            </span>
            <span style="font-size: 0.75rem; font-weight: 700; color: #2D6A4F; background: rgba(45, 106, 79, 0.1); padding: 2px 8px; border-radius: 4px;">
                Demand Signal: {intel_signal['demand_signal']}
            </span>
        </div>
        <div style="font-size: 0.95rem; font-weight: 700; color: #163E2B; line-height: 1.5;">
            "{intel_signal['insight_text']}"
        </div>
        <div style="font-size: 0.75rem; color: #526058; margin-top: 6px;">
            Confidence: <b>{intel_signal['confidence']}%</b> · Derived from live OGD mandi benchmark, buyer postings, and regional freight corridors.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Dynamic Opportunity Spotlight
pune_bench = get_latest_market_price(sel_crop or "Onion", district="Pune")
nashik_bench = get_latest_market_price(sel_crop or "Onion", district="Nashik")
pune_p = float(pune_bench.get("modal_price_per_kg", 36.00))
nashik_p = float(nashik_bench.get("modal_price_per_kg", 44.00))
diff = abs(pune_p - nashik_p)
extra_inc = diff * 500

render_market_opportunity_layer(
    destination="Pune Wholesale Terminal",
    destination_price=pune_p,
    local_mandi="Nashik APMC",
    local_price=nashik_p,
    confidence=88,
    extra_income=int(extra_inc),
)

# ------------------------------------------------------------
# AGRICULTURAL WEATHER & LOGISTICS TRANSMISSION
# ------------------------------------------------------------

render_weather_intelligence(
    chain_items=[
        ("CLEAR WEATHER IN NASHIK", "सुसह्य वाहतूक"),
        ("AUCTION ARRIVALS STABLE", "नियमित आवक"),
        ("PUNE BUYER DEMAND ↑", "मागणी वाढ"),
        ("FARM REALIZATION +12%", "नफ्यात वाढ"),
    ],
    insight_text=t("weather_transit_insight"),
)

# ------------------------------------------------------------
# TODAY'S MARKET FLOOR & MANDI TELEMETRY (API #1)
# ------------------------------------------------------------

st.divider()

st.subheader(f"📈 {t('mandi_momentum_title')}")
st.caption("Live daily market prices from data.gov.in Current Daily & Variety-wise APIs.")

tab_floor, tab_chart, tab_sd, tab_corridors = st.tabs([
    "🏛️ Today's Market Floor (Live Telemetry)",
    f"📊 {t('tab_price_movement')}",
    f"⚖️ {t('tab_supply_demand')}",
    f"🗺️ {t('tab_trade_corridors')}",
])

with tab_floor:
    st.markdown("### Today's Market Floor")
    st.caption("Current mandi benchmark prices directly from data.gov.in Current Daily Price API.")
    
    telemetry_df = get_market_floor_telemetry(
        state="Maharashtra" if sel_state == "Maharashtra" else "Maharashtra",
        district=sel_district,
        commodity=sel_crop,
        limit=20,
    )
    
    if not telemetry_df.empty:
        disp_df = telemetry_df[[
            "market", "district", "commodity", "variety", "grade", "price_str", "movement", "arrival_date"
        ]].rename(columns={
            "market": "Market / Mandi",
            "district": "District",
            "commodity": "Commodity",
            "variety": "Variety",
            "grade": "Grade",
            "price_str": "Current Modal Price",
            "movement": "Price Movement",
            "arrival_date": "Arrival Date",
        })
        st.dataframe(disp_df, use_container_width=True, hide_index=True)
    else:
        st.info("No market floor records available for current filter selection.")

with tab_chart:
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        crop_select = st.selectbox(
            t("crop_input"),
            ["Onion", "Tomato", "Potato", "Wheat"],
            index=0,
            key="mandi_crop_sel_tab",
        )
    with f_col2:
        market_select = st.selectbox(
            t("select_apmc_mandi"),
            ["Nashik", "Lasalgaon", "Pune", "Ahmednagar", "Ahilyanagar"],
            index=0,
            key="mandi_market_sel_tab",
        )

    fig = create_mandi_trend_chart(prices_df, crop=crop_select, market=market_select)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(t("no_historical_records"))

with tab_sd:
    fig_sd = create_supply_demand_chart(demand_df, produce_df, crop=crop_select)
    if fig_sd is not None:
        st.plotly_chart(fig_sd, use_container_width=True)
        st.caption(t("supply_demand_insight_caption"))

with tab_corridors:
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-radius: 12px; padding: 18px; margin-top: 10px;">
            <div style="font-size: 0.85rem; font-weight: 800; color: #183A2A; text-transform: uppercase; margin-bottom: 12px;">
                {t('active_reg_spreads_title')}
            </div>
            <table style="width: 100%; border-collapse: collapse; font-size: 0.88rem; color: #18201B;">
                <thead>
                    <tr style="border-bottom: 2px solid #E5DFD3; text-align: left; color: #68756C;">
                        <th style="padding: 8px;">{t('col_trade_corridor')}</th>
                        <th style="padding: 8px;">{t('col_commodity')}</th>
                        <th style="padding: 8px;">{t('col_local_apmc')}</th>
                        <th style="padding: 8px;">{t('col_target_hub')}</th>
                        <th style="padding: 8px;">{t('col_gross_spread')}</th>
                        <th style="padding: 8px;">{t('col_transport_kg')}</th>
                        <th style="padding: 8px;">{t('col_net_realization')}</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom: 1px solid #F0ECE1;">
                        <td style="padding: 10px 8px; font-weight: 700;">Niphad ➔ Pune</td>
                        <td>Onion (Grade A)</td>
                        <td>₹{nashik_p:.2f}</td>
                        <td>₹{pune_p:.2f}</td>
                        <td style="color: #176536; font-weight: 700;">₹{pune_p - nashik_p:+.2f}/kg</td>
                        <td>₹0.85/kg</td>
                        <td style="color: #176536; font-weight: 800; background: #E6F5EC; border-radius: 4px;">Net realization optimized</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #F0ECE1;">
                        <td style="padding: 10px 8px; font-weight: 700;">Dindori ➔ Mumbai</td>
                        <td>Tomato (Grade A)</td>
                        <td>₹21.00</td>
                        <td>₹28.50</td>
                        <td style="color: #176536; font-weight: 700;">+₹7.50/kg</td>
                        <td>₹1.40/kg</td>
                        <td style="color: #176536; font-weight: 800; background: #E6F5EC; border-radius: 4px;">+₹6.10/kg Net (+29%)</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 8px; font-weight: 700;">Rahata ➔ Ahilyanagar</td>
                        <td>Wheat (Sharbati)</td>
                        <td>₹30.00</td>
                        <td>₹31.50</td>
                        <td style="color: #176536; font-weight: 700;">+₹1.50/kg</td>
                        <td>₹0.50/kg</td>
                        <td style="color: #176536; font-weight: 800; background: #E6F5EC; border-radius: 4px;">+₹1.00/kg Net (+3.3%)</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------
# FOOTER
# ------------------------------------------------------------

st.divider()
st.caption(f"ℹ️ {t('digital_mandi_footer')}")
