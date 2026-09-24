"""
AI Market Match & Buyer Discovery | Kisan Setu
Theme: 'Bharat, Reimagined'
Decision-Oriented Experience answering: 'WHO SHOULD I SELL TO, AND WHY?'
Reuses: ai.matching, ai.demand_forecasting, gemini.explanation, maps.route_map, utils.transactions, utils.voice_assistant
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date

from utils.data_loader import (
    load_demand,
    load_produce,
    load_buyers,
    load_logistics,
    load_prices,
    load_farmers,
    load_transactions,
)

from ai.matching import find_matches
from ai.demand_forecasting import forecast_demand_with_market_context
from ai.pricing import get_mandi_market_benchmark
from utils.demand_data import build_transaction_demand_history
from utils.setu_intelligence import calculate_setu_intelligence
from utils.quality_intelligence import calculate_quality_intelligence
from logistics.partner_manager import get_partner_for_transaction
from maps.route_map import display_optimized_route_map
from utils.translations import t, get_current_language
from gemini.explanation import explain_buyer_match
from utils.transactions import create_transaction
from utils.voice_assistant import render_kisan_bol

from ui.theme import inject_custom_theme
from ui.setu_components import (
    render_brand_header,
    render_bharat_market_pulse,
    render_html,
)

# ============================================================
# THEME INJECTION & LANGUAGE RESOLUTION
# ============================================================

inject_custom_theme()
language = get_current_language()

# ============================================================
# LOAD CORE DATASETS
# ============================================================

produce_df = load_produce()
buyers_df = load_buyers()
logistics_df = load_logistics()
prices_df = load_prices()
demand_df = load_demand()
farmers_df = load_farmers()
transactions_df = load_transactions()

# Build platform transaction-derived demand history
transaction_demand_df = build_transaction_demand_history(
    transactions_df=transactions_df,
    produce_df=produce_df,
)

# Resolve Active User & Farmer Profile
user_id = st.session_state.get("user_id", "F001")
user_name = st.session_state.get("user_name", "Ramesh Patil")
if not str(user_id).startswith("F"):
    user_id = "F001"

farmer_row = farmers_df[farmers_df["farmer_id"].astype(str).str.strip().str.upper() == str(user_id).strip().upper()]
if not farmer_row.empty:
    f_info = farmer_row.iloc[0]
    farmer_location = f"{f_info.get('village', 'Niphad')}, {f_info.get('district', 'Nashik')}"
else:
    farmer_location = "Niphad, Nashik"

# Resolve Farmer's Produce Lots
farmer_produce = produce_df[produce_df["farmer_id"].astype(str).str.strip().str.upper() == str(user_id).strip().upper()]
if farmer_produce.empty and not produce_df.empty:
    farmer_produce = produce_df

# Session state initialization
if "selected_produce_id" not in st.session_state or (not farmer_produce.empty and st.session_state.selected_produce_id not in farmer_produce["produce_id"].values):
    st.session_state.selected_produce_id = farmer_produce["produce_id"].iloc[0] if not farmer_produce.empty else "P001"

if "selected_match_buyer_id" not in st.session_state:
    st.session_state.selected_match_buyer_id = None

if "confirming_deal_buyer_id" not in st.session_state:
    st.session_state.confirming_deal_buyer_id = None

if "show_route_map" not in st.session_state:
    st.session_state.show_route_map = False

if "show_kisan_bol_panel" not in st.session_state:
    st.session_state.show_kisan_bol_panel = False

if "last_created_tx_id" not in st.session_state:
    st.session_state.last_created_tx_id = None

if "last_created_tx_info" not in st.session_state:
    st.session_state.last_created_tx_info = None

# ============================================================
# 1. HEADER & MARKET PULSE
# ============================================================

render_bharat_market_pulse()

render_brand_header(
    title=t("ai_market_match_title"),
    subtitle=t("ai_market_match_sub"),
    badge=t("badge_ai_active"),
)

# ============================================================
# 2. PRODUCE LOT SELECTION & CONTEXT
# ============================================================

if farmer_produce.empty:
    st.info(f"🌾 {t('add_produce_prompt')}")
    if st.button(f"➕ {t('btn_create_new_lot')}", type="primary"):
        st.switch_page("pages/list_produce.py")
    st.stop()

# Lot selector if multiple lots exist
col_lot_picker, col_lot_chip = st.columns([1.8, 2.2])

with col_lot_picker:
    lot_options = farmer_produce["produce_id"].tolist()
    cur_pid = st.session_state.selected_produce_id
    idx = lot_options.index(cur_pid) if cur_pid in lot_options else 0
    
    selected_pid = st.selectbox(
        f"🏷️ {t('selected_lot_label')}",
        options=lot_options,
        index=idx,
        format_func=lambda x: f"{farmer_produce[farmer_produce['produce_id']==x].iloc[0]['crop']} ({int(float(farmer_produce[farmer_produce['produce_id']==x].iloc[0]['quantity_kg']))} kg, Grade {farmer_produce[farmer_produce['produce_id']==x].iloc[0]['quality_grade']}) — #{x}",
        key="active_produce_lot_dropdown",
    )
    if selected_pid != st.session_state.selected_produce_id:
        st.session_state.selected_produce_id = selected_pid
        st.session_state.selected_match_buyer_id = None
        st.session_state.confirming_deal_buyer_id = None
        st.session_state.show_route_map = False
        st.rerun()

selected_produce = farmer_produce[farmer_produce["produce_id"] == st.session_state.selected_produce_id].iloc[0]

produce_qty = float(selected_produce.get("quantity_kg", 500))
produce_expected_price = float(selected_produce.get("expected_price_per_kg", 30))
crop_name = str(selected_produce.get("crop", "Onion"))
grade_str = str(selected_produce.get("quality_grade", "A"))
lot_location = str(selected_produce.get("location", "Niphad"))
lot_district = str(selected_produce.get("district", "Nashik"))
lot_avail_date = str(selected_produce.get("available_date", "2026-09-10"))

# Crop Icon Lookup
crop_icons = {
    "onion": "🧅",
    "tomato": "🍅",
    "potato": "🥔",
    "wheat": "🌾",
    "banana": "🍌",
    "ginger": "🫚",
    "rice": "🍚",
}
crop_icon = crop_icons.get(crop_name.lower(), "🌱")

with col_lot_chip:
    st.markdown(f"<div style='height: 28px;'></div>", unsafe_allow_html=True)
    chip_html = f"""
    <div style="background: rgba(22, 62, 43, 0.06); border: 1px solid rgba(22, 62, 43, 0.16); border-radius: 10px; padding: 8px 14px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
        <span style="font-weight: 800; color: #163E2B; font-size: 0.95rem;">{crop_icon} {crop_name} · {produce_qty:,.0f} kg · Grade {grade_str}</span>
        <span style="font-size: 0.82rem; color: #526058; font-weight: 600;">📍 {lot_location}, {lot_district}</span>
    </div>
    """
    render_html(chip_html)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# ============================================================
# 3. RUN MATCHING ENGINE (find_matches)
# ============================================================

# Resolve regional demand dataset hierarchy (1. Historical dataset, 2. Platform transactions, 3. Unavailable)
target_dist_clean = str(lot_district).strip().lower()
target_crop_clean = str(crop_name).strip().lower()

selected_demand_df = None
demand_source = "Unavailable"

# Step 1: Check data/demand.csv for >= 3 observations
if demand_df is not None and not demand_df.empty:
    req_cols = {"date", "district", "crop", "demand_quantity_kg"}
    if req_cols.issubset(set(demand_df.columns)):
        hist_subset = demand_df[
            (demand_df["district"].astype(str).str.strip().str.lower() == target_dist_clean) &
            (demand_df["crop"].astype(str).str.strip().str.lower() == target_crop_clean)
        ]
        if len(hist_subset) >= 3:
            selected_demand_df = demand_df
            demand_source = "Historical demand dataset"

# Step 2: Fallback to transaction_demand_df if >= 3 observations exist (DO NOT concatenate)
if selected_demand_df is None and transaction_demand_df is not None and not transaction_demand_df.empty:
    tx_subset = transaction_demand_df[
        (transaction_demand_df["district"].astype(str).str.strip().str.lower() == target_dist_clean) &
        (transaction_demand_df["crop"].astype(str).str.strip().str.lower() == target_crop_clean)
    ]
    if len(tx_subset) >= 3:
        selected_demand_df = transaction_demand_df
        demand_source = "Platform transaction history"

forecast_horizon_days = int(st.session_state.get("farmer_fc_horizon_days", 3))
if selected_demand_df is not None:
    forecast = forecast_demand_with_market_context(
        demand_df=selected_demand_df,
        district=lot_district,
        crop=crop_name,
        forecast_days=forecast_horizon_days,
        market_prices_df=prices_df,
    )
else:
    forecast = None

if forecast is not None:
    forecast["demand_source"] = demand_source
forecast_kg = forecast["forecast_demand_kg"] if forecast is not None else None

matches = find_matches(selected_produce, buyers_df, forecast_demand=forecast_kg)

# Mandi Modal Price benchmark from Government data.gov.in API with fallback
mandi_bench = get_mandi_market_benchmark(commodity=crop_name, district=lot_district, state="Maharashtra")
market_modal_price = float(mandi_bench.get("modal_price_per_kg", 28.40))
mandi_min_price = float(mandi_bench.get("min_price_per_kg", market_modal_price))
mandi_max_price = float(mandi_bench.get("max_price_per_kg", market_modal_price))
mandi_market_name = str(mandi_bench.get("market", f"{lot_district} APMC"))
mandi_arrival_date = str(mandi_bench.get("arrival_date", date.today().strftime("%Y-%m-%d")))
mandi_variety = str(mandi_bench.get("variety", "FAQ"))
mandi_grade = str(mandi_bench.get("grade", "Local"))
mandi_is_live = bool(mandi_bench.get("is_live", False))
mandi_source = str(mandi_bench.get("source", "data.gov.in AGMARKNET API"))

# Logistics rate lookup
matching_logistics = logistics_df[logistics_df["location"].astype(str).str.lower() == lot_district.lower()]
selected_logistics = matching_logistics.iloc[0] if not matching_logistics.empty else logistics_df.iloc[0]
cost_per_km = float(selected_logistics.get("cost_per_km", 4.5))
base_cost = float(selected_logistics.get("base_cost", 300.0))

# ============================================================
# 4. HANDLE NO-MATCH STATE
# ============================================================

if matches.empty:
    with st.container(border=True):
        st.warning(f"⚠️ **{t('no_suitable_match_title')}**")
        st.markdown(f"*{t('no_suitable_match_desc')}*")
        st.caption(f"Crop: **{crop_name}** | Volume: **{produce_qty:,.0f} kg** | Grade: **{grade_str}** | Location: **{lot_location}, {lot_district}**")
        
        btn_nm1, btn_nm2 = st.columns(2)
        with btn_nm1:
            if st.button(f"🏪 {t('btn_view_digital_mandi')}", type="primary", use_container_width=True):
                st.switch_page("pages/digital_mandi.py")
        with btn_nm2:
            if st.button(f"🎙️ {t('btn_ask_kisan_bol')}", use_container_width=True):
                st.session_state.show_kisan_bol_panel = True
                st.rerun()

    if st.session_state.get("show_kisan_bol_panel", False):
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        with st.expander(f"🎙️ {t('kisan_bol_title')} — {t('kisan_bol_caption')}", expanded=True):
            render_kisan_bol(user_role="Farmer", user_profile=st.session_state)
    st.stop()

# ============================================================
# 5. RESOLVE ACTIVE/SELECTED BUYER
# ============================================================

# Default to top ranked match if no specific buyer selected
selected_bid = st.session_state.get("selected_match_buyer_id")
match_rows = matches[matches["buyer_id"] == selected_bid] if selected_bid else pd.DataFrame()
if not match_rows.empty:
    active_buyer = match_rows.iloc[0]
else:
    active_buyer = matches.iloc[0]
    st.session_state.selected_match_buyer_id = active_buyer["buyer_id"]

buyer_id_val = str(active_buyer["buyer_id"])
buyer_name_val = str(active_buyer.get("buyer_name", active_buyer.get("name", "Pune Fresh Retail")))
buyer_type_val = str(active_buyer.get("buyer_type", "Retailer"))
buyer_loc_val = str(active_buyer.get("location", active_buyer.get("district", "Pune")))
buyer_district_val = str(active_buyer.get("district", "Pune"))
buyer_req_qty = float(active_buyer.get("required_quantity_kg", 600))
buyer_max_price = float(active_buyer.get("max_price_per_kg", 31.0))
match_score = int(float(active_buyer.get("match_score", 94)))
distance_km = float(active_buyer.get("distance_km", 145))

# Lookup original buyer record for min_quality requirement
raw_buyer_match = buyers_df[buyers_df["buyer_id"].astype(str) == buyer_id_val]
buyer_min_qual = raw_buyer_match.iloc[0].get("min_quality", "A") if not raw_buyer_match.empty else "A"

# Financials
gross_realization = produce_qty * buyer_max_price
transport_cost = base_cost + (distance_km * cost_per_km)
net_realization = max(0.0, gross_realization - transport_cost)
effective_price = net_realization / produce_qty if produce_qty > 0 else 0
potential_diff = buyer_max_price - market_modal_price
total_potential_diff = potential_diff * produce_qty

# Setu Intelligence decision-support synthesis
setu_intel = calculate_setu_intelligence(
    produce_lot=selected_produce,
    mandi_benchmark=mandi_bench,
    buyer_match=active_buyer,
    demand_forecast=forecast,
    logistics=selected_logistics,
    custom_logistics_cost=transport_cost,
)

# Helper: Duplicate Order Check
def check_existing_active_order(produce_id, buyer_id=None):
    df_tx = load_transactions()
    if df_tx.empty or "produce_id" not in df_tx.columns:
        return None
    active_statuses = {"order placed", "confirmed", "in transit", "pending"}
    matches = df_tx[
        (df_tx["produce_id"].astype(str).str.strip() == str(produce_id).strip()) &
        (df_tx["status"].astype(str).str.strip().str.lower().isin(active_statuses))
    ]
    if matches.empty:
        return None
    if buyer_id:
        buyer_matches = matches[matches["buyer_id"].astype(str).str.strip() == str(buyer_id).strip()]
        if not buyer_matches.empty:
            return buyer_matches.iloc[-1].to_dict()
    return matches.iloc[-1].to_dict()

# ============================================================
# 6. TRANSACTION CONFIRMATION MODAL / DRAWER
# ============================================================

if st.session_state.get("confirming_deal_buyer_id") == buyer_id_val:
    existing_order = check_existing_active_order(selected_produce["produce_id"], buyer_id_val)
    if existing_order:
        with st.container(border=True):
            st.warning(f"⚠️ **{t('already_ordered_title')}**")
            st.markdown(t("already_ordered_msg", order_id=existing_order.get("transaction_id", "T000"), buyer_name=buyer_name_val))
            
            e_col1, e_col2 = st.columns(2)
            with e_col1:
                st.markdown(f"**📋 {t('order_id_label')}:** #{existing_order.get('transaction_id')}")
                st.markdown(f"**🛒 {t('buyer_label')}:** {buyer_name_val}")
            with e_col2:
                st.markdown(f"**🌾 {t('produce_label')}:** {crop_name} ({float(existing_order.get('quantity_kg', produce_qty)):,.0f} kg)")
                st.markdown(f"**📊 {t('status_label')}:** `{existing_order.get('status')}`")

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            btn_eo1, btn_eo2 = st.columns(2)
            with btn_eo1:
                if st.button(f"📦 {t('btn_view_active_order')} →", type="primary", use_container_width=True, key="btn_view_existing_order"):
                    st.switch_page("pages/farmer_orders.py")
            with btn_eo2:
                if st.button(f"✕ {t('close')}", use_container_width=True, key="btn_close_existing_notice"):
                    st.session_state.confirming_deal_buyer_id = None
                    st.rerun()
        st.divider()
    else:
        with st.container(border=True):
            st.warning(f"🤝 **{t('confirm_deal_title')}**")
            st.markdown(f"*{t('confirm_deal_subtitle')}*")
            
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                st.markdown(f"**🌾 {t('harvest_label')}:** {crop_name} · {produce_qty:,.0f} kg (Grade {grade_str})")
                st.markdown(f"**🛒 {t('buyer_label')}:** {buyer_name_val} ({buyer_type_val})")
                st.markdown(f"**🚚 {t('delivery_label')}:** {lot_location}, {lot_district} ➔ {buyer_loc_val} ({distance_km:.0f} km)")
            with c_col2:
                st.markdown(f"**💰 {t('price_label')}:** ₹{buyer_max_price:.2f}/kg (Total: ₹{gross_realization:,.0f})")
                st.markdown(f"**📈 {t('potential_spread_label')}:** +₹{potential_diff:.2f}/kg vs Mandi Benchmark")
                st.markdown(f"**🚚 {t('estimated_freight_label')}:** ₹{transport_cost:,.0f} (Net: ₹{net_realization:,.0f})")

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            btn_c1, btn_c2 = st.columns(2)
            with btn_c1:
                if st.button(f"🤝 {t('btn_confirm_create_order')}", type="primary", use_container_width=True, key="btn_accept_and_create_order"):
                    active_dup = check_existing_active_order(selected_produce["produce_id"], buyer_id_val)
                    if active_dup:
                        st.session_state.confirming_deal_buyer_id = buyer_id_val
                        st.rerun()
                    else:
                        new_tx = create_transaction(
                            farmer_id=selected_produce["farmer_id"],
                            buyer_id=buyer_id_val,
                            produce_id=selected_produce["produce_id"],
                            quantity_kg=produce_qty,
                            price_per_kg=buyer_max_price,
                        )
                        st.session_state.confirming_deal_buyer_id = None
                        st.session_state.last_created_tx_info = {
                            "order_id": new_tx["transaction_id"],
                            "buyer_name": buyer_name_val,
                            "crop": crop_name,
                            "quantity_kg": produce_qty,
                            "price_per_kg": buyer_max_price,
                            "total_value": gross_realization,
                        }
                        st.session_state.last_created_tx_id = new_tx["transaction_id"]
                        st.rerun()
            with btn_c2:
                if st.button(f"✕ {t('btn_cancel_deal')}", use_container_width=True, key="btn_cancel_deal_confirm"):
                    st.session_state.confirming_deal_buyer_id = None
                    st.rerun()
        st.divider()

# Handle post-creation success state
if st.session_state.get("last_created_tx_info"):
    last_tx = st.session_state.last_created_tx_info
    with st.container(border=True):
        st.success(f"✓ **{t('order_created_title')}**")
        st.markdown(f"*{t('order_initiated_success_desc')}*")
        
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            st.markdown(f"**📋 {t('order_id_label')}:** #{last_tx['order_id']}")
            st.markdown(f"**🛒 {t('buyer_label')}:** {last_tx['buyer_name']}")
            st.markdown(f"**🌾 {t('produce_label')}:** {last_tx['crop']}")
        with s_col2:
            st.markdown(f"**⚖️ {t('quantity_label')}:** {last_tx['quantity_kg']:,.0f} kg")
            st.markdown(f"**💰 {t('price_label')}:** ₹{last_tx['price_per_kg']:.2f}/kg")
            st.markdown(f"**💵 {t('total_value_label')}:** ₹{last_tx['total_value']:,.0f}")

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        btn_s1, btn_s2 = st.columns(2)
        with btn_s1:
            if st.button(f"📦 {t('btn_view_active_order')} →", type="primary", use_container_width=True, key="btn_view_active_order_success"):
                st.switch_page("pages/farmer_orders.py")
        with btn_s2:
            if st.button(f"✕ {t('close')}", use_container_width=True, key="btn_close_order_success"):
                st.session_state.last_created_tx_info = None
                st.session_state.last_created_tx_id = None
                st.rerun()
    st.divider()

# ============================================================
# 7. DOMINANT CARD: BEST AVAILABLE OPPORTUNITY
# ============================================================

is_top_rec = (active_buyer["buyer_id"] == matches.iloc[0]["buyer_id"])
badge_text = t("recommended_match_badge") if is_top_rec else t("buyer_match_label").upper()

opp_card_html = f"""
<div style="background: linear-gradient(145deg, #163E2B 0%, #1E5128 55%, #163E2B 100%); color: #FFFFFF; border-radius: 20px; padding: 26px 30px; margin-bottom: 1.2rem; box-shadow: 0 14px 36px rgba(22, 62, 43, 0.22); border: 1.5px solid rgba(217, 119, 6, 0.4); position: relative; overflow: hidden;">
    <div style="position: absolute; right: -30px; top: -30px; width: 160px; height: 160px; background: radial-gradient(circle, rgba(217, 119, 6, 0.25) 0%, transparent 70%); border-radius: 50%; pointer-events: none;"></div>
    
    <div style="position: relative; z-index: 1;">
        <!-- Card Header Badge -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
            <span style="font-size: 0.76rem; font-weight: 900; letter-spacing: 0.08em; text-transform: uppercase; background: linear-gradient(135deg, #E5A010 0%, #D97706 100%); color: #FFFFFF; padding: 5px 14px; border-radius: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
                {t('best_available_opportunity_title')}
            </span>
            <span style="font-size: 0.8rem; font-weight: 800; color: #86EFAC; background: rgba(0,0,0,0.25); padding: 4px 12px; border-radius: 12px; border: 1px solid rgba(134,239,172,0.3);">
                ✦ {match_score}% MATCH · {badge_text}
            </span>
        </div>

        <!-- Buyer Name & Type -->
        <div style="font-size: 1.75rem; font-weight: 900; color: #FFFFFF; margin-bottom: 4px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
            <span>🛒 {buyer_name_val}</span>
            <span style="font-size: 1.0rem; font-weight: 600; color: #D7B982;">({buyer_type_val} · {buyer_loc_val})</span>
        </div>

        <!-- Offered Price & Potential Realization -->
        <div style="display: flex; align-items: baseline; gap: 18px; flex-wrap: wrap; margin-bottom: 14px;">
            <div style="font-size: 2.1rem; font-weight: 900; color: #F7E9B7;">
                ₹{buyer_max_price:.2f} <span style="font-size: 1.0rem; font-weight: 600; color: #E5DFD3;">/ kg</span>
            </div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #E5DFD3;">
                {t('potential_realization_label')}: <strong style="color: #FFFFFF;">₹{gross_realization:,.0f}</strong>
            </div>
        </div>

        <!-- Benchmark & Spread Row -->
        <div style="display: flex; gap: 20px; flex-wrap: wrap; font-size: 0.90rem; color: #E5DFD3; border-top: 1px solid rgba(255,255,255,0.14); padding-top: 12px;">
            <span>🏛️ {t('mandi_reference_price')}: <strong>₹{market_modal_price:.2f}/kg</strong></span>
            <span>📈 {t('potential_spread_label')}: <strong style="color: #FCD34D;">+{('+' if potential_diff>=0 else '')}₹{potential_diff:.2f}/kg (+₹{total_potential_diff:,.0f})</strong></span>
            <span>🚚 {t('estimated_distance_label')}: <strong>{distance_km:.0f} km</strong></span>
        </div>
    </div>
</div>
"""
render_html(opp_card_html)

# Primary CTA Buttons
btn_col_a, btn_col_b = st.columns([1.8, 1.2])

with btn_col_a:
    if st.button(f"🤝 {t('btn_accept_match')} →", type="primary", use_container_width=True, key="btn_accept_match_hero"):
        st.session_state.confirming_deal_buyer_id = buyer_id_val
        st.rerun()

with btn_col_b:
    if st.button(f"{t('btn_ask_kisan_bol')}", use_container_width=True, key="btn_ask_kb_hero"):
        st.session_state.show_kisan_bol_panel = not st.session_state.get("show_kisan_bol_panel", False)
        st.rerun()

if st.session_state.get("show_kisan_bol_panel", False):
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    with st.expander(f"🎙️ {t('kisan_bol_title')} — {t('kisan_bol_caption')}", expanded=True):
        render_kisan_bol(user_role="Farmer", user_profile=st.session_state)

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# ============================================================
# 8. SECTION: WHY THIS BUYER? (MATCH REASONS & BREAKDOWN)
# ============================================================

st.subheader(f"💡 {t('why_this_buyer_title')}")

# 6 Factor Explanations Grid
reasons_html = f"""
<div style="background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(12px); border: 1px solid rgba(22, 62, 43, 0.12); border-radius: 14px; padding: 18px 20px; margin-bottom: 1.2rem; box-shadow: 0 4px 14px rgba(22, 62, 43, 0.04);">
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; font-size: 0.88rem; color: #163E2B;">
        <div>✓ <strong>{t('factor_qty_compat')}:</strong> {t('factor_qty_reason', qty=int(produce_qty), req_qty=int(buyer_req_qty))}</div>
        <div>✓ <strong>{t('factor_quality_compat')}:</strong> {t('factor_qual_reason', farmer_grade=grade_str, buyer_grade=buyer_min_qual)}</div>
        <div>✓ <strong>{t('factor_price_compat')}:</strong> {t('factor_price_reason', buyer_price=f"{buyer_max_price:.2f}", expected_price=f"{produce_expected_price:.2f}")}</div>
        <div>✓ <strong>{t('factor_demand')}:</strong> {t('factor_demand_reason')}</div>
        <div>✓ <strong>{t('factor_distance')}:</strong> {t('factor_distance_reason', distance=int(distance_km))}</div>
        <div>✓ <strong>{t('factor_timing')}:</strong> {t('factor_timing_reason')}</div>
    </div>
</div>
"""
render_html(reasons_html)

# Collapsible Detailed Match Breakdown & Gemini AI Explanation
with st.expander(f"▼ {t('why_kisan_setu_recommends_buyer')}", expanded=False):
    # Transparent breakdown table
    b_col1, b_col2 = st.columns(2)
    with b_col1:
        st.markdown(f"**{t('factor_price_compat')}:** `{t('rating_strong')}` (₹{buyer_max_price:.2f}/kg vs ₹{produce_expected_price:.2f}/kg)")
        st.markdown(f"**{t('factor_qty_compat')}:** `{t('rating_strong')}` ({int(produce_qty)} kg / {int(buyer_req_qty)} kg)")
        st.markdown(f"**{t('factor_quality_compat')}:** `{t('rating_strong')}` (Grade {grade_str} meets Grade {buyer_min_qual})")
    with b_col2:
        st.markdown(f"**{t('factor_distance')}:** `{t('rating_good')}` ({distance_km:.0f} km {lot_district} ➔ {buyer_district_val})")
        st.markdown(f"**{t('factor_demand')}:** `{t('rating_high')}` (Buyer Match Alignment: {match_score}%)")
        st.markdown(f"**{t('factor_timing')}:** `{t('rating_good')}` (Delivery window matched)")

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    
    with st.spinner(t("generating_ai_explanation")):
        ai_narrative = explain_buyer_match(
            crop=crop_name,
            quantity=produce_qty,
            quality=grade_str,
            farmer_location=farmer_location,
            buyer_name=buyer_name_val,
            buyer_type=buyer_type_val,
            buyer_quantity=buyer_req_qty,
            buyer_price=buyer_max_price,
            distance=distance_km,
            match_score=match_score,
            language=language,
        )
    st.info(ai_narrative)

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# ============================================================
# 9. SECTION: BUYER INFORMATION & PRICE INTELLIGENCE
# ============================================================

col_b_info, col_p_intel = st.columns(2)

with col_b_info:
    with st.container(border=True):
        st.subheader(f"🛒 {t('buyer_info_title')}")
        st.markdown(f"**{t('buyer_name_label')}:** {buyer_name_val}")
        st.markdown(f"**{t('buyer_type_label')}:** {buyer_type_val}")
        st.markdown(f"**{t('buyer_location_label')}:** {buyer_loc_val}, {buyer_district_val}")
        st.markdown(f"**{t('buyer_required_qty_label')}:** {buyer_req_qty:,.0f} kg")
        st.markdown(f"**{t('buyer_min_quality_label')}:** Grade {buyer_min_qual}")
        st.markdown(f"**{t('buyer_max_price_label')}:** ₹{buyer_max_price:.2f}/kg")
        st.markdown(f"**{t('buyer_demand_label')}:** `{t('demand_high')}` ({buyer_req_qty:,.0f} kg requirement)")

with col_p_intel:
    with st.container(border=True):
        st.subheader(f"📈 {t('price_intelligence_title')}")
        
        pi1, pi2 = st.columns(2)
        pi1.metric(t("mandi_benchmark_label"), f"₹{market_modal_price:.2f}/kg")
        pi2.metric(t("buyer_offer_label"), f"₹{buyer_max_price:.2f}/kg", f"+₹{potential_diff:.2f}/kg")
        
        st.markdown(f"**{t('potential_spread_label')}:** +₹{potential_diff:.2f}/kg")
        st.markdown(f"**{t('potential_difference_total')}:** +₹{total_potential_diff:,.0f} ({t('for_total_qty', default='for total')}: {produce_qty:,.0f} kg)")
        
        # Government data.gov.in Mandi Market Intelligence
        with st.expander(f"🏛️ Mandi Market Intelligence ({crop_name} · {lot_district})", expanded=True):
            source_badge = "🟢 Live data.gov.in API" if mandi_is_live else "📁 Cached Market Data"
            st.caption(f"**Data Provenance:** {source_badge}")
            
            mi_c1, mi_c2 = st.columns(2)
            with mi_c1:
                st.markdown(f"• **Commodity:** {crop_name}")
                st.markdown(f"• **District:** {lot_district}")
                st.markdown(f"• **Market:** {mandi_market_name}")
                st.markdown(f"• **Arrival Date:** {mandi_arrival_date}")
            with mi_c2:
                st.markdown(f"• **Latest Mandi Benchmark:** ₹{market_modal_price:.2f}/kg")
                st.markdown(f"• **Minimum:** ₹{mandi_min_price:.2f}/kg")
                st.markdown(f"• **Maximum:** ₹{mandi_max_price:.2f}/kg")
                st.markdown(f"• **Variety / Grade:** {mandi_variety} (Grade {mandi_grade})")
        
        st.caption(f"ℹ️ *{t('spread_disclaimer', default='Mandi modal price is an indicative regional market benchmark; buyer offer represents a direct farm-gate purchase agreement.')}*")

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# ============================================================
# 10. SECTION: DEMAND OUTLOOK (AI-POWERED FORECASTING)
# ============================================================

with st.container(border=True):
    do_col_title, do_col_horizon = st.columns([2.8, 1.2])
    with do_col_title:
        st.subheader(f"📈 {t('demand_outlook_title', default='Demand Outlook')} ({crop_name} · {lot_district})")
    with do_col_horizon:
        horizon_selection = st.radio(
            "Forecast Horizon",
            options=[3, 7],
            format_func=lambda x: f"{x}-Day Outlook",
            horizontal=True,
            key="farmer_fc_horizon_selector",
            label_visibility="collapsed",
            index=0 if forecast_horizon_days == 3 else 1,
        )
        if horizon_selection != forecast_horizon_days:
            st.session_state.farmer_fc_horizon_days = horizon_selection
            st.rerun()

    if forecast is not None:
        fc_current = float(forecast.get("current_demand_kg", 0.0))
        fc_projected = float(forecast.get("forecast_demand_kg", 0.0))
        fc_trend = str(forecast.get("trend", "Stable"))
        fc_pct_change = float(forecast.get("percentage_change", 0.0))
        fc_days = int(forecast.get("history_days", 0))
        fc_quality = str(forecast.get("data_quality", "Moderate"))
        fc_explanation = str(forecast.get("explanation", ""))
        fc_values = forecast.get("forecast_values", [])
        mkt_ctx = forecast.get("market_price_context")

        # Telemetry metrics row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current Demand", f"{fc_current:,.0f} kg")
        m2.metric(f"{forecast_horizon_days}-Day Forecast", f"{fc_projected:,.0f} kg", f"{fc_pct_change:+.1f}%")
        m3.metric("Market Trend", fc_trend)
        m4.metric("Data Quality", f"{fc_quality} ({fc_days}d)")

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # Dynamic Explanation Callout
        st.info(f"💡 **AI Forecast Insight:** {fc_explanation}")

        # Demand source provenance badge & platform limitation disclaimer
        if demand_source == "Platform transaction history":
            st.caption("🏷️ **Demand source:** Kisan Setu platform transactions")
            st.caption("ℹ️ *Note: Transaction-derived demand represents Kisan Setu platform activity, not total regional market demand.*")
        elif demand_source == "Historical demand dataset":
            st.caption("🏷️ **Demand source:** Historical demand dataset")
        else:
            st.caption(f"🏷️ **Demand source:** {demand_source}")

        # Forecast values visual representation
        col_fc_chart, col_fc_details = st.columns([2, 1.3])
        
        with col_fc_chart:
            if fc_values:
                chart_df = pd.DataFrame({
                    "Forecast Day": [f"Day +{i+1}" for i in range(len(fc_values))],
                    "Projected Demand (kg)": fc_values
                }).set_index("Forecast Day")
                st.bar_chart(chart_df, height=180, color="#163E2B")

        with col_fc_details:
            st.caption("📋 **Daily Projected Demand:**")
            for i, val in enumerate(fc_values):
                st.markdown(f"• **Day +{i+1}:** `{val:,.0f} kg`")
            
            if mkt_ctx and mkt_ctx.get("latest_modal_price_per_kg"):
                m_price = mkt_ctx.get("latest_modal_price_per_kg")
                m_cnt = mkt_ctx.get("mandi_records_count", 0)
                st.caption(f"🏛️ **Current Mandi Benchmark:** ₹{m_price:.2f}/kg ({m_cnt} mandi records)")

    else:
        st.info(
            f"ℹ️ Demand outlook is unavailable for **{crop_name}** in **{lot_district}** "
            "because insufficient historical observations are available in the regional demand series."
        )
        st.caption("🏷️ *Demand forecast unavailable* · The AI matching engine continues to evaluate buyer requirement orders directly.")

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# ============================================================
# 11. SECTION: SETU INTELLIGENCE (DECISION-SUPPORT ENGINE)
# ============================================================

with st.container(border=True):
    st.subheader(f"🧠 {t('setu_intelligence_title', default='Setu Intelligence')} ({crop_name} · {lot_district})")
    st.caption("Factual direct buyer opportunity vs. regional mandi benchmark synthesis")

    si_mandi_modal = setu_intel.get("mandi_modal_price_per_kg")
    si_buyer_offer = setu_intel.get("buyer_offer_price_per_kg")
    si_logistics = setu_intel.get("logistics_cost", 0.0)
    si_net_realization = setu_intel.get("estimated_net_realization", 0.0)
    si_effective_net = setu_intel.get("effective_net_per_kg", 0.0)
    si_spread = setu_intel.get("price_spread_per_kg")
    si_net_diff = setu_intel.get("net_difference")
    si_demand_signal = setu_intel.get("demand_signal", "Unavailable")
    si_demand_source = setu_intel.get("demand_source", "Unavailable")
    si_demand_pct = setu_intel.get("demand_percentage_change")
    si_explanation = setu_intel.get("explanation", "")
    si_factors = setu_intel.get("decision_factors", {})
    freight_per_kg = (si_logistics / produce_qty) if produce_qty > 0 else 0.0

    # 4 compact telemetry cards
    si_m1, si_m2, si_m3, si_m4 = st.columns(4)

    with si_m1:
        st.metric(
            label="Live Mandi Benchmark",
            value=f"₹{si_mandi_modal:.2f}/kg" if si_mandi_modal is not None else "N/A",
            help="Latest AGMARKNET / data.gov.in modal price for the district",
        )
        st.caption(f"🏛️ {setu_intel.get('mandi_market', f'{lot_district} APMC')}")

    with si_m2:
        spread_str = f"{'+' if si_spread and si_spread >= 0 else ''}₹{si_spread:.2f}/kg" if si_spread is not None else None
        st.metric(
            label="Buyer Offer",
            value=f"₹{si_buyer_offer:.2f}/kg" if si_buyer_offer is not None else "N/A",
            delta=spread_str,
            help="Agreed direct purchase price from matched buyer",
        )
        st.caption(f"🛒 {buyer_name_val}")

    with si_m3:
        st.metric(
            label="Estimated Logistics",
            value=f"₹{si_logistics:,.0f}",
            delta=f"-₹{freight_per_kg:.2f}/kg",
            delta_color="inverse",
            help="Estimated freight cost based on transport distance",
        )
        st.caption(f"🚚 {distance_km:.0f} km route")

    with si_m4:
        st.metric(
            label="Estimated Net",
            value=f"₹{si_net_realization:,.0f}",
            delta=f"₹{si_effective_net:.2f}/kg net",
            help="Estimated net farm-gate realization after deducting logistics cost",
        )
        st.caption(f"🌾 For {produce_qty:,.0f} kg")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 3 Structured Intelligence Pillars
    p_col1, p_col2, p_col3 = st.columns(3)

    with p_col1:
        st.markdown("**📊 Demand Signal**")
        if si_demand_signal == "Increasing":
            pct_txt = f" ({'+' if (si_demand_pct or 0) >= 0 else ''}{si_demand_pct:.1f}%)" if si_demand_pct is not None else ""
            st.success(f"🟢 **Increasing**{pct_txt}")
        elif si_demand_signal == "Stable":
            pct_txt = f" ({'+' if (si_demand_pct or 0) >= 0 else ''}{si_demand_pct:.1f}%)" if si_demand_pct is not None else ""
            st.info(f"🟡 **Stable**{pct_txt}")
        elif si_demand_signal == "Decreasing":
            pct_txt = f" ({'+' if (si_demand_pct or 0) >= 0 else ''}{si_demand_pct:.1f}%)" if si_demand_pct is not None else ""
            st.warning(f"🔴 **Decreasing**{pct_txt}")
        else:
            st.caption("⚪ **Unavailable**")
        st.caption(f"Source: *{si_demand_source}*")

    with p_col2:
        st.markdown("**⚖️ Market Comparison**")
        if si_net_diff is not None:
            sign = "+" if si_net_diff >= 0 else ""
            st.markdown(f"**Net Spread:** `{sign}₹{si_spread:.2f}/kg`" if si_spread is not None else "")
            st.markdown(f"**Net Differential:** `{sign}₹{si_net_diff:,.0f}`")
        else:
            st.caption("Benchmark comparison unavailable")
        st.caption("Compared with mandi modal benchmark")

    with p_col3:
        st.markdown("**🚚 Logistics Impact**")
        st.markdown(f"**Distance:** `{distance_km:.0f} km`")
        st.markdown(f"**Freight Overhead:** `-₹{freight_per_kg:.2f}/kg`")
        st.caption(f"Effective net: ₹{si_effective_net:.2f}/kg")

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # Dynamic Factual Explanation & Decision Factors
    st.info(f"💡 **Setu Intelligence Synthesis:** {si_explanation}")

    # Quality Context
    farmer_quality_intel = calculate_quality_intelligence(
        quality_grade=grade_str,
        minimum_quality=buyer_min_qual,
        crop=crop_name,
        assessment=selected_produce.get("quality_assessment", selected_produce.get("ai_quality_assessment", None))
    )

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    st.markdown("**🔍 QUALITY CONTEXT**")
    qc1, qc2, qc3 = st.columns(3)
    with qc1:
        st.markdown(f"**Quality Grade:** `Grade {farmer_quality_intel['quality_grade'] or 'N/A'}`")
    with qc2:
        st.markdown(f"**Buyer Requirement:** `Grade {farmer_quality_intel['required_quality'] or 'N/A'}`")
    with qc3:
        if farmer_quality_intel['quality_status'] == "Requirement met":
            st.markdown("**Requirement Status:** `✓ Met`")
        elif farmer_quality_intel['quality_status'] == "Requirement not met":
            st.markdown("**Requirement Status:** `✕ Not Met`")
        else:
            st.markdown("**Requirement Status:** `Unavailable`")

    if farmer_quality_intel.get("assessment_available"):
        with st.expander("🔬 AI Quality Observation", expanded=False):
            st.caption(f"ℹ️ *{farmer_quality_intel['disclaimer']}*")
            st.markdown(farmer_quality_intel["assessment_text"])
            st.caption(f"Source: {farmer_quality_intel['assessment_source']}")

    with st.expander("📋 Decision Factors & Provenance Breakdown", expanded=False):
        for factor_key, factor_desc in si_factors.items():
            factor_label = factor_key.replace("_", " ").title()
            st.markdown(f"• **{factor_label}:** {factor_desc}")
        st.caption("ℹ️ *All valuations are indicative estimates based on current buyer agreements and live market data. Kisan Setu does not guarantee market transactions.*")

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# ============================================================
# 12. SECTION: DELIVERY & LOGISTICS
# ============================================================

with st.container(border=True):
    st.subheader(f"🚚 {t('delivery_logistics_title')}")
    
    st.markdown(f"**{lot_location}, {lot_district}** ➔ **{buyer_loc_val}** ({distance_km:.0f} km)")
    
    l1, l2, l3 = st.columns(3)
    l1.metric(t("estimated_distance_label"), f"{distance_km:.0f} km")
    l2.metric(t("estimated_freight_label"), f"₹{transport_cost:,.0f}", f"-₹{transport_cost/produce_qty:.2f}/kg", delta_color="inverse")
    l3.metric(t("net_realization_label"), f"₹{net_realization:,.0f}", f"₹{effective_price:.2f}/kg net")

    # LOGISTICS FULFILMENT SUMMARY
    # Check if there is a transaction associated with this produce lot
    matching_produce_id = str(selected_produce.get("produce_id", selected_pid if "selected_pid" in locals() else ""))
    matching_txs = transactions_df[transactions_df["produce_id"].astype(str) == matching_produce_id] if matching_produce_id else pd.DataFrame()
    assigned_partner_info = None
    if not matching_txs.empty:
        active_tx_id = str(matching_txs.iloc[-1]["transaction_id"])
        assigned_partner_info = get_partner_for_transaction(active_tx_id)

    st.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px dashed #E5DFD3;' />", unsafe_allow_html=True)
    st.markdown("**🚚 LOGISTICS FULFILMENT**")
    
    if assigned_partner_info:
        lf1, lf2 = st.columns(2)
        with lf1:
            st.markdown(f"**📍 Pickup Location:** {assigned_partner_info.get('pickup_location', f'{lot_location}, {lot_district}')}")
            st.markdown(f"**🏢 Buyer Destination:** {assigned_partner_info.get('destination', buyer_loc_val)}")
            st.markdown(f"**🚚 Distance:** {float(assigned_partner_info.get('distance_km', distance_km)):.0f} km")
        with lf2:
            st.markdown(f"**💰 Estimated Freight:** ₹{float(assigned_partner_info.get('estimated_freight', transport_cost)):,.0f}")
            st.markdown(f"**🚛 Assigned Partner:** {assigned_partner_info.get('partner_name')} ({assigned_partner_info.get('vehicle', 'Mini Truck')})")
            st.markdown(f"**📦 Delivery Status:** `🟢 {assigned_partner_info.get('status', 'Assigned')}`")
    else:
        st.markdown(
            f"""
            <div style="background: #FFFDF8; border: 1px solid #E5DFD3; border-radius: 8px; padding: 10px 14px; font-size: 0.84rem; color: #68756C;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span>📍 <b>Pickup:</b> {lot_location}, {lot_district} ➔ 🏢 <b>Destination:</b> {buyer_loc_val} ({distance_km:.0f} km)</span>
                    <span style="font-weight: 700; color: #B45309;">⏳ Awaiting logistics assignment</span>
                </div>
                <div style="margin-top: 4px; font-size: 0.80rem;">
                    Estimated Transport Freight: ₹{transport_cost:,.0f} (₹{transport_cost/produce_qty:.2f}/kg) · <i>Will be coordinated once match is accepted.</i>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    
    if st.button(f"🗺️ {t('btn_hide_route') if st.session_state.show_route_map else t('btn_view_route')}", key="toggle_route_map_btn"):
        st.session_state.show_route_map = not st.session_state.show_route_map
        st.rerun()

    if st.session_state.get("show_route_map", False):
        display_optimized_route_map(
            route=[lot_location, buyer_loc_val],
            farmer_names={lot_location: user_name},
            buyer_name=buyer_name_val,
            crop=crop_name,
            total_distance_km=distance_km,
            total_load_kg=produce_qty,
            logistics_cost=transport_cost,
        )

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# ============================================================
# 13. SECTION: AVAILABLE BUYER MATCHES (IF MULTIPLE)
# ============================================================

if len(matches) > 1:
    st.subheader(f"🤝 {t('available_buyer_matches_title')}")
    st.caption(t("other_matches_count_label", count=len(matches) - 1))

    for idx, m_row in matches.iterrows():
        b_id = str(m_row["buyer_id"])
        b_name = str(m_row.get("buyer_name", m_row.get("name", "Buyer")))
        b_type = str(m_row.get("buyer_type", "Wholesaler"))
        b_loc = str(m_row.get("location", m_row.get("district", "Pune")))
        b_price = float(m_row.get("max_price_per_kg", 30.0))
        b_score = int(float(m_row.get("match_score", 90)))
        b_dist = float(m_row.get("distance_km", 140))
        b_req = float(m_row.get("required_quantity_kg", 500))

        is_currently_selected = (b_id == buyer_id_val)

        with st.container(border=True):
            mc1, mc2, mc3 = st.columns([2.5, 1.5, 1.2])
            with mc1:
                st.markdown(f"**🛒 {b_name}** ({b_type}) {'✦ **[ACTIVE]**' if is_currently_selected else ''}")
                st.caption(f"📍 {b_loc} ({b_dist:.0f} km) · {t('buyer_required_qty_label')}: {b_req:,.0f} kg")
            with mc2:
                st.markdown(f"💰 **₹{b_price:.2f}/kg** · ⭐ **{b_score}% Match**")
                st.caption(f"{t('potential_realization_label')}: ₹{produce_qty * b_price:,.0f}")
            with mc3:
                if is_currently_selected:
                    st.button(f"✓ Selected", key=f"btn_sel_{b_id}_{idx}", disabled=True, use_container_width=True)
                else:
                    if st.button(f"👉 {t('btn_select_this_buyer')}", key=f"btn_sel_{b_id}_{idx}", use_container_width=True):
                        st.session_state.selected_match_buyer_id = b_id
                        st.session_state.confirming_deal_buyer_id = None
                        st.session_state.show_route_map = False
                        st.rerun()

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# ============================================================
# 14. KISAN BOL CONTEXTUAL PROMPT
# ============================================================

st.markdown(
    f"""
    <div style="background: linear-gradient(135deg, rgba(22, 62, 43, 0.05) 0%, rgba(217, 119, 6, 0.06) 100%), #FFFFFF; border: 1.5px solid rgba(22, 62, 43, 0.16); border-radius: 16px; padding: 18px 22px; margin-bottom: 1.2rem; box-shadow: 0 4px 14px rgba(22, 62, 43, 0.04);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
            <div style="font-size: 0.90rem; font-weight: 800; color: #163E2B;">
                🎙️ {t('kisan_bol_match_prompt')}
            </div>
            <div>
                <span style="font-size: 0.72rem; font-weight: 800; background: #163E2B; color: #FFFFFF; padding: 3px 10px; border-radius: 6px;">
                    {t('kisan_bol_title')}
                </span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

if st.button(f"🎙️ {t('btn_ask_kisan_bol')}", use_container_width=True, key="btn_kisan_bol_bottom"):
    st.session_state.show_kisan_bol_panel = not st.session_state.get("show_kisan_bol_panel", False)
    st.rerun()

st.divider()
st.caption(f"ℹ️ {t('farmer_footer_caption')}")