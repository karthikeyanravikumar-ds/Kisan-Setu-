"""
Agricultural Market Intelligence Center (Government / Admin) | Kisan Setu
Theme: 'Bharat, Reimagined'
Macro Market Health, Anomaly Detection, Regional Heatmap & Supply-Demand Equilibrium
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from utils.data_loader import (
    load_farmers,
    load_buyers,
    load_produce,
    load_prices,
    load_demand,
    load_feedback,
)
from utils.transactions import load_transactions
from utils.consumer_orders import load_consumer_orders

from ui.theme import inject_custom_theme
from ui.setu_components import (
    render_brand_header,
    render_bharat_market_pulse,
    render_setu_pulse,
    render_weather_intelligence,
    render_learning_performance_section,
)
from ui.charts import (
    create_supply_demand_chart,
    create_mandi_trend_chart,
)
from utils.learning_loop import calculate_learning_summary
from utils.translations import t, get_current_language

# =========================================================
# THEME INJECTION
# =========================================================

inject_custom_theme()

language = get_current_language()

# Load Data
farmers = load_farmers()
buyers = load_buyers()
produce = load_produce()
prices = load_prices()
demand = load_demand()
feedback = load_feedback()
transactions = load_transactions()
consumer_orders = load_consumer_orders()

# Clean Data
if not prices.empty:
    d_col = "date" if "date" in prices.columns else ("arrival_date" if "arrival_date" in prices.columns else None)
    if d_col:
        prices["date"] = pd.to_datetime(prices[d_col], errors="coerce")
    for col in ["min_price_per_kg", "modal_price_per_kg", "max_price_per_kg"]:
        if col in prices.columns:
            prices[col] = pd.to_numeric(prices[col], errors="coerce")

# Top Banner
render_bharat_market_pulse()

# Brand Header with Logo
render_brand_header(
    title=f"{t('brand_admin_title')}",
    subtitle=t("brand_admin_sub"),
    badge=t("badge_admin_overview"),
)

# Editorial Header
st.markdown(
    f"""
    <div style="background: linear-gradient(135deg, #133324 0%, #0C2117 100%); color: #F5F0E6; border-radius: 16px; padding: 24px 28px; margin-bottom: 1.5rem; box-shadow: 0 6px 24px rgba(12, 33, 23, 0.25); border: 1px solid rgba(229, 160, 16, 0.25);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div>
                <div style="font-size: 0.74rem; font-weight: 800; color: #FACC15; letter-spacing: 0.08em; text-transform: uppercase;">
                    ✦ {t('state_intel_unit_title')}
                </div>
                <div style="font-family: 'Cinzel', 'Playfair Display', Georgia, serif; font-size: 2.15rem; font-weight: 900; color: #F59E0B; margin: 4px 0 6px 0; letter-spacing: -0.01em; text-shadow: 0 2px 10px rgba(0,0,0,0.5);">
                    {t('agri_market_intel_center')}
                </div>
                <div style="font-size: 0.95rem; color: #FDE68A; font-weight: 500;">
                    {t('pilot_region')} · Comprehensive Agro-Economic Telemetry
                </div>
            </div>
            <div style="text-align: right; background: rgba(255, 253, 248, 0.08); border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 10px; padding: 8px 18px;">
                <div style="font-size: 0.7rem; color: #FDE68A; text-transform: uppercase; font-weight: 800;">{t('live_telemetry_badge')}</div>
                <div style="font-size: 1.05rem; font-weight: 900; color: #4ADE80;">● {t('active_monitoring_badge')}</div>
                <div style="font-size: 0.75rem; color: #E5DFD3;">{datetime.now().strftime("%d %b %Y · %I:%M %p")}</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Dynamic benchmark average
dynamic_avg = 38.00
try:
    from data_ingestion.market_data import get_latest_market_price
    dynamic_avg = float(get_latest_market_price("Onion").get("modal_price_per_kg", 38.00))
except Exception:
    pass

# Setu Macro Pulse Ribbon
render_setu_pulse(
    farmers_count=len(farmers),
    avg_price=dynamic_avg,
    buyers_count=len(buyers),
    fulfilment_rate=94,
)

# =========================================================
# 1. MARKET HEALTH GAUGES
# =========================================================

st.markdown(
    f"""
    <div style="font-size: 0.8rem; font-weight: 800; color: #183A2A; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;">
        ✦ {t('macro_market_health_title')}
    </div>
    """,
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-top: 4px solid #176536; border-radius: 10px; padding: 14px 16px; box-shadow: 0 2px 8px rgba(24,32,27,0.03);">
            <div style="font-size: 0.72rem; font-weight: 700; color: #68756C; text-transform: uppercase;">{t('supply_health_label')}</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #176536; margin: 4px 0;">82%</div>
            <div style="font-size: 0.78rem; color: #68756C;">{t('supply_health_desc')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-top: 4px solid #E8B83D; border-radius: 10px; padding: 14px 16px; box-shadow: 0 2px 8px rgba(24,32,27,0.03);">
            <div style="font-size: 0.72rem; font-weight: 700; color: #68756C; text-transform: uppercase;">{t('demand_velocity_label')}</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #B85C38; margin: 4px 0;">↑ 14%</div>
            <div style="font-size: 0.78rem; color: #68756C;">{t('demand_velocity_desc')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-top: 4px solid #183A2A; border-radius: 10px; padding: 14px 16px; box-shadow: 0 2px 8px rgba(24,32,27,0.03);">
            <div style="font-size: 0.72rem; font-weight: 700; color: #68756C; text-transform: uppercase;">{t('price_stability_label')}</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #183A2A; margin: 4px 0;">↑ 6.2%</div>
            <div style="font-size: 0.78rem; color: #68756C;">{t('price_stability_desc')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-top: 4px solid #1952B3; border-radius: 10px; padding: 14px 16px; box-shadow: 0 2px 8px rgba(24,32,27,0.03);">
            <div style="font-size: 0.72rem; font-weight: 700; color: #68756C; text-transform: uppercase;">{t('logistics_setu_score_label')}</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #1952B3; margin: 4px 0;">94/100</div>
            <div style="font-size: 0.78rem; color: #68756C;">{t('logistics_setu_score_desc')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# 2. AREAS REQUIRING ATTENTION (Anomalies)
# =========================================================

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
st.subheader(f"⚠️ {t('areas_req_attention_title')}")

anom_col1, anom_col2 = st.columns(2)

with anom_col1:
    st.markdown(
        f"""
        <div style="background: #FFFDF8; border: 1px solid #E5DFD3; border-left: 4px solid #E8B83D; border-radius: 8px; padding: 14px 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <b style="color: #18201B; font-size: 0.95rem;">{t('anom1_title')}</b>
                <span style="background: #FFF4DC; color: #91610A; font-size: 0.72rem; font-weight: 800; padding: 2px 8px; border-radius: 4px;">{t('surplus_badge')}</span>
            </div>
            <div style="font-size: 0.85rem; color: #68756C; margin-top: 6px; line-height: 1.4;">
                {t('anom1_desc')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with anom_col2:
    st.markdown(
        f"""
        <div style="background: #FFFDF8; border: 1px solid #E5DFD3; border-left: 4px solid #B85C38; border-radius: 8px; padding: 14px 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <b style="color: #18201B; font-size: 0.95rem;">{t('anom2_title')}</b>
                <span style="background: #FDEEE9; color: #9E4932; font-size: 0.72rem; font-weight: 800; padding: 2px 8px; border-radius: 4px;">{t('deficit_badge')}</span>
            </div>
            <div style="font-size: 0.85rem; color: #68756C; margin-top: 6px; line-height: 1.4;">
                {t('anom2_desc')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Weather Transmission
render_weather_intelligence(
    chain_items=[
        ("MONSOON CLEARANCE IN WESTERN GHATS", "हवामान स्थिरता"),
        ("NH60 HIGHWAY PASSABLE", "सुरळीत वाहतूक"),
        ("SUPPLY CHANNELS EXPANDING", "विस्तारित मार्ग"),
        ("INTERMEDIARY MARKUP: ZERO", "शून्य मध्यस्थ"),
    ],
    insight_text=t("weather_transit_insight"),
)

st.divider()

# =========================================================
# 3. REGIONAL MARKET HEATMAP / MATRIX
# =========================================================

st.subheader(f"🗺️ {t('regional_agri_matrix_title')}")
st.caption(t("regional_agri_matrix_caption"))

st.markdown(
    f"""
    <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-radius: 12px; padding: 18px; margin-bottom: 1rem;">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.88rem; color: #18201B;">
            <thead>
                <tr style="border-bottom: 2px solid #E5DFD3; text-align: left; color: #68756C;">
                    <th style="padding: 10px;">{t('matrix_col_district')}</th>
                    <th style="padding: 10px;">{t('matrix_col_commodity')}</th>
                    <th style="padding: 10px;">{t('matrix_col_supply')}</th>
                    <th style="padding: 10px;">{t('matrix_col_demand')}</th>
                    <th style="padding: 10px;">{t('matrix_col_modal_price')}</th>
                    <th style="padding: 10px;">{t('matrix_col_signal')}</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid #F0ECE1;">
                    <td style="padding: 12px 10px; font-weight: 800; color: #183A2A;">Nashik (नाशिक)</td>
                    <td>Onion (कांदा) & Tomato</td>
                    <td><span style="color: #176536; font-weight: 700;">High (उच्च आवक)</span></td>
                    <td>Moderate</td>
                    <td>₹28.40/kg</td>
                    <td><span style="background: #FFF4DC; color: #91610A; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.75rem;">EXPORT SURPLUS</span></td>
                </tr>
                <tr style="border-bottom: 1px solid #F0ECE1;">
                    <td style="padding: 12px 10px; font-weight: 800; color: #183A2A;">Ahmednagar (अहमदनगर)</td>
                    <td>Tomato & Wheat</td>
                    <td><span style="color: #9E4932; font-weight: 700;">Tight (तुटवडा)</span></td>
                    <td>High (वाढती मागणी)</td>
                    <td>₹34.20/kg</td>
                    <td><span style="background: #FDEEE9; color: #9E4932; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.75rem;">DRAW INVENTORY</span></td>
                </tr>
                <tr style="border-bottom: 1px solid #F0ECE1;">
                    <td style="padding: 12px 10px; font-weight: 800; color: #183A2A;">Pune (पुणे)</td>
                    <td>All Commodities</td>
                    <td>Moderate</td>
                    <td><span style="color: #176536; font-weight: 700;">Very High (+14%)</span></td>
                    <td>₹31.00/kg</td>
                    <td><span style="background: #E6F5EC; color: #176536; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.75rem;">ACTIVE SETU LOAD HUB</span></td>
                </tr>
                <tr>
                    <td style="padding: 12px 10px; font-weight: 800; color: #183A2A;">Mumbai (मुंबई)</td>
                    <td>Wholesale Terminal</td>
                    <td>External Import</td>
                    <td><span style="color: #176536; font-weight: 700;">Maximum</span></td>
                    <td>₹38.50/kg</td>
                    <td><span style="background: #E8F0FE; color: #1952B3; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.75rem;">HIGH REALIZATION SPREAD</span></td>
                </tr>
            </tbody>
        </table>
    </div>
    """,
    unsafe_allow_html=True,
)

# Charts Section
st.subheader(f"📊 {t('macro_supply_demand_analytics')}")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    fig_sd = create_supply_demand_chart(demand, produce, crop="Onion")
    if fig_sd:
        st.plotly_chart(fig_sd, use_container_width=True)

with chart_col2:
    fig_pr = create_mandi_trend_chart(prices, crop="Onion", market="Nashik")
    if fig_pr:
        st.plotly_chart(fig_pr, use_container_width=True)

st.divider()

# =========================================================
# 4. LEARNING & PERFORMANCE TELEMETRY
# =========================================================

learning_summary = calculate_learning_summary(
    transactions_df=transactions,
    feedback_df=feedback,
    produce_df=produce,
    prices_df=prices,
    demand_df=demand,
)
render_learning_performance_section(learning_summary)

st.divider()
st.caption(f"ℹ️ {t('admin_footer_caption')}")