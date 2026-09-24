"""
Buyer Procurement Terminal | Kisan Setu
Theme: 'Bharat, Reimagined'
Decision-Oriented B2B Procurement Hub: 'What produce do I need, what is available, and which farmer lots match my requirement?'
Reuses: ai.matching, maps.route_map, utils.transactions, utils.data_loader, utils.translations
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date

from utils.data_loader import (
    load_buyers,
    load_farmers,
    load_produce,
    load_logistics,
    load_prices,
    load_demand,
    load_buyer_requirements,
)
from utils.transactions import (
    load_transactions,
    create_transaction,
    update_transaction_status,
)
from ai.matching import calculate_match_score, get_distance
from ai.demand_forecasting import forecast_demand
from ai.pricing import get_mandi_market_benchmark
from utils.demand_data import get_regional_demand_series
from utils.buyer_intelligence import calculate_buyer_intelligence
from utils.quality_intelligence import calculate_quality_intelligence
from maps.route_map import display_optimized_route_map
from utils.translations import t, get_current_language

from ui.theme import inject_custom_theme
from ui.setu_components import (
    render_brand_header,
    render_bharat_market_pulse,
    render_farm_passport,
    render_empty_state,
    render_html,
)

# ============================================================
# 1. THEME & INITIALIZATION
# ============================================================

inject_custom_theme()
language = get_current_language()

# Load Core Data
buyers_df = load_buyers()
farmers_df = load_farmers()
produce_df = load_produce()
transactions_df = load_transactions()
logistics_df = load_logistics()
prices_df = load_prices()
demand_df = load_demand()
requirements_df = load_buyer_requirements()

# Resolve Active Buyer Session
current_user_id = st.session_state.get("user_id", "B001")
if not str(current_user_id).startswith("B"):
    current_user_id = "B001"

buyer_options = buyers_df["buyer_id"].tolist() if not buyers_df.empty else ["B001"]
default_b_idx = buyer_options.index(current_user_id) if current_user_id in buyer_options else 0

# Session state keys
if "buyer_confirming_lot_id" not in st.session_state:
    st.session_state.buyer_confirming_lot_id = None

if "buyer_selected_lot_id" not in st.session_state:
    st.session_state.buyer_selected_lot_id = None

if "buyer_show_route_lot_id" not in st.session_state:
    st.session_state.buyer_show_route_lot_id = None

if "buyer_show_passport_lot_id" not in st.session_state:
    st.session_state.buyer_show_passport_lot_id = None

if "buyer_last_created_tx" not in st.session_state:
    st.session_state.buyer_last_created_tx = None

# ============================================================
# 2. BRAND HEADER & TOP BANNER
# ============================================================

render_bharat_market_pulse()

render_brand_header(
    title=t("buyer_hub_header"),
    subtitle=t("buyer_hub_subtitle"),
    badge=t("badge_buyer_active"),
)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# ============================================================
# 3. ACTIVE BUYER IDENTITY
# ============================================================

col_b_sel, col_b_meta = st.columns([1.8, 2.2])

with col_b_sel:
    selected_buyer_id = st.selectbox(
        f"🏢 {t('active_buyer_account')}",
        buyer_options,
        index=default_b_idx,
        format_func=lambda x: f"{x} · {buyers_df[buyers_df['buyer_id']==x].iloc[0]['name']} ({buyers_df[buyers_df['buyer_id']==x].iloc[0]['location']})" if not buyers_df.empty and x in buyers_df['buyer_id'].values else str(x),
        key="active_buyer_dropdown",
    )
    if selected_buyer_id != current_user_id:
        st.session_state.user_id = selected_buyer_id
        st.session_state.buyer_confirming_lot_id = None
        st.session_state.buyer_selected_lot_id = None
        st.session_state.buyer_show_route_lot_id = None
        st.rerun()

buyer_row = buyers_df[buyers_df["buyer_id"] == selected_buyer_id].iloc[0] if not buyers_df.empty and selected_buyer_id in buyers_df["buyer_id"].values else buyers_df.iloc[0]

buyer_name = str(buyer_row.get("name", "Pune Fresh Retail"))
buyer_type = str(buyer_row.get("buyer_type", "Retailer"))
buyer_loc = str(buyer_row.get("location", "Pune"))
buyer_district = str(buyer_row.get("district", "Pune"))
buyer_crop = str(buyer_row.get("crop", "Onion"))
buyer_req_qty = float(buyer_row.get("required_quantity_kg", 550))
buyer_min_qual = str(buyer_row.get("min_quality", "A"))
buyer_max_price = float(buyer_row.get("max_price_per_kg", 38))
buyer_req_date = str(buyer_row.get("required_date", "2026-09-11"))

with col_b_meta:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    chip_html = f"""
    <div style="background: rgba(22, 62, 43, 0.06); border: 1px solid rgba(22, 62, 43, 0.16); border-radius: 10px; padding: 8px 14px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
        <span style="font-weight: 800; color: #163E2B; font-size: 0.95rem;">🏢 {buyer_name} · <span style="font-weight:600; color:#526058;">{buyer_type}</span></span>
        <span style="font-size: 0.82rem; color: #526058; font-weight: 600;">📍 {buyer_loc}, {buyer_district}</span>
    </div>
    """
    render_html(chip_html)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# ============================================================
# 4. PROCUREMENT SNAPSHOT (REAL DATA KPIS)
# ============================================================

# Real Metric Calculations
buyer_txs = transactions_df[transactions_df["buyer_id"].astype(str) == str(selected_buyer_id)].copy()
active_orders_cnt = len(buyer_txs[buyer_txs["status"].astype(str).isin(["Order Placed", "Confirmed", "In Transit", "Delivered"])])
completed_orders_cnt = len(buyer_txs[buyer_txs["status"].astype(str) == "Completed"])

# Buyer Requirements count
buyer_reqs = requirements_df[requirements_df["buyer_id"].astype(str) == str(selected_buyer_id)] if not requirements_df.empty else pd.DataFrame()
active_reqs_cnt = len(buyer_reqs[buyer_reqs["status"].astype(str).str.lower() == "active"]) if not buyer_reqs.empty else 1

# Available Matches count (available produce with matching crop)
available_produce = produce_df[produce_df["status"].astype(str).str.lower() == "available"].copy()
matching_crop_lots = available_produce[available_produce["crop"].astype(str).str.lower() == buyer_crop.lower()]
available_matches_cnt = len(matching_crop_lots)

k1, k2, k3, k4 = st.columns(4)
k1.metric(f"📋 {t('active_requirements_label')}", active_reqs_cnt)
k2.metric(f"🎯 {t('available_matches_label')}", available_matches_cnt)
k3.metric(f"🚚 {t('active_orders_label')}", active_orders_cnt)
k4.metric(f"✅ {t('completed_orders_label')}", completed_orders_cnt)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# ============================================================
# 5. WHAT DO YOU NEED TODAY? (ACTIVE REQUIREMENT BANNER)
# ============================================================

crop_icons = {
    "onion": "🧅",
    "tomato": "🍅",
    "potato": "🥔",
    "wheat": "🌾",
    "banana": "🍌",
    "ginger": "🫚",
    "rice": "🍚",
}
crop_icon = crop_icons.get(buyer_crop.lower(), "🌱")

req_card_html = f"""
<div style="background: linear-gradient(135deg, #163E2B 0%, #1E5128 65%, #163E2B 100%); color: #FFFFFF; border-radius: 18px; padding: 22px 26px; margin-bottom: 1.2rem; box-shadow: 0 10px 28px rgba(22, 62, 43, 0.2); border: 1.5px solid rgba(217, 119, 6, 0.4);">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px;">
        <span style="font-size: 0.74rem; font-weight: 900; letter-spacing: 0.08em; text-transform: uppercase; background: linear-gradient(135deg, #E5A010 0%, #D97706 100%); color: #FFFFFF; padding: 4px 12px; border-radius: 20px;">
            {t('what_do_you_need_today')}
        </span>
        <span style="font-size: 0.80rem; font-weight: 700; color: #86EFAC; background: rgba(0,0,0,0.25); padding: 4px 12px; border-radius: 12px; border: 1px solid rgba(134,239,172,0.3);">
            📅 {t('target_delivery_date')}: {buyer_req_date}
        </span>
    </div>
    
    <div style="font-size: 1.65rem; font-weight: 900; color: #FFFFFF; margin-bottom: 6px; display: flex; align-items: center; gap: 10px;">
        <span>{crop_icon} {buyer_crop.upper()}</span>
        <span style="font-size: 0.95rem; font-weight: 600; color: #D7B982;">({buyer_req_qty:,.0f} kg · {t('min_grade_label', grade=buyer_min_qual)})</span>
    </div>

    <div style="display: flex; gap: 24px; flex-wrap: wrap; font-size: 0.90rem; color: #E5DFD3; border-top: 1px solid rgba(255,255,255,0.15); padding-top: 10px; margin-top: 8px;">
        <span>💰 {t('max_budget_price')}: <strong style="color: #F7E9B7;">₹{buyer_max_price:.2f}/kg</strong></span>
        <span>📍 {t('delivery_hub_loc')}: <strong style="color: #FFFFFF;">{buyer_loc}, {buyer_district}</strong></span>
        <span>🎯 {t('available_matches_label')}: <strong style="color: #86EFAC;">{available_matches_cnt} Lots</strong></span>
    </div>
</div>
"""
render_html(req_card_html)

# Requirement CTAs
btn_rc1, btn_rc2 = st.columns([1.5, 1.5])
with btn_rc1:
    if st.button(f"🔎 {t('find_produce_btn')} / {t('btn_find_matches')}", type="primary", use_container_width=True, key="btn_find_produce_hero"):
        st.session_state.scroll_to_matches = True
with btn_rc2:
    if st.button(f"📝 {t('btn_edit_requirement')}", use_container_width=True, key="btn_edit_req_hero"):
        st.switch_page("pages/buyer_requirements.py")

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# ============================================================
# 6. DUPLICATE TRANSACTION & CONFIRMATION HELPERS
# ============================================================

def check_existing_active_order_for_produce(produce_id):
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
    return matches.iloc[-1].to_dict()

# Logistics Rate Lookup
matching_logistics = logistics_df[logistics_df["location"].astype(str).str.lower() == buyer_district.lower()]
selected_logistics = matching_logistics.iloc[0] if not matching_logistics.empty else (logistics_df.iloc[0] if not logistics_df.empty else {})
cost_per_km = float(selected_logistics.get("cost_per_km", 4.5))
base_freight = float(selected_logistics.get("base_cost", 300.0))

# ============================================================
# 7. ORDER CONFIRMATION MODAL & SUCCESS STATES
# ============================================================

# Modal Drawer when Buyer clicked [ REQUEST / ACCEPT PROCUREMENT ]
if st.session_state.get("buyer_confirming_lot_id"):
    c_lot_id = st.session_state.buyer_confirming_lot_id
    c_lot_match = produce_df[produce_df["produce_id"].astype(str) == str(c_lot_id)]
    
    if not c_lot_match.empty:
        c_lot = c_lot_match.iloc[0]
        c_crop = str(c_lot.get("crop", buyer_crop))
        c_qty = float(c_lot.get("quantity_kg", 500))
        c_grade = str(c_lot.get("quality_grade", "A"))
        c_price = float(c_lot.get("expected_price_per_kg", 30))
        c_farmer_id = str(c_lot.get("farmer_id", "F001"))
        c_farmer_loc = str(c_lot.get("location", "Niphad"))
        c_farmer_dist = str(c_lot.get("district", "Nashik"))
        
        # Lookup Farmer Name
        f_match = farmers_df[farmers_df["farmer_id"].astype(str) == c_farmer_id]
        c_farmer_name = f_match.iloc[0]["name"] if not f_match.empty else f"Farmer {c_farmer_id}"
        
        c_distance = get_distance(c_farmer_dist, buyer_district)
        c_freight = base_freight + (c_distance * cost_per_km)
        c_total_val = c_qty * c_price
        
        # Check Duplicate
        existing_tx = check_existing_active_order_for_produce(c_lot_id)
        if existing_tx:
            with st.container(border=True):
                st.warning(f"⚠️ **{t('already_ordered_title')}**")
                st.markdown(t("already_ordered_msg", order_id=existing_tx.get("transaction_id", "T000"), buyer_name=buyer_name))
                
                ed_c1, ed_c2 = st.columns(2)
                with ed_c1:
                    st.markdown(f"**📋 {t('order_id_label')}:** #{existing_tx.get('transaction_id')}")
                    st.markdown(f"**🌾 {t('produce_label')}:** {c_crop} ({c_qty:,.0f} kg)")
                with ed_c2:
                    st.markdown(f"**💰 {t('price_label')}:** ₹{float(existing_tx.get('price_per_kg', c_price)):.2f}/kg")
                    st.markdown(f"**📊 {t('status_label')}:** `{existing_tx.get('status')}`")

                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                b_btn1, b_btn2 = st.columns(2)
                with b_btn1:
                    if st.button(f"✕ {t('close')}", use_container_width=True, key="btn_close_dup_buyer"):
                        st.session_state.buyer_confirming_lot_id = None
                        st.rerun()
            st.divider()
        else:
            with st.container(border=True):
                st.warning(f"🤝 **{t('confirm_procurement_title')}**")
                st.markdown(f"*{t('confirm_procurement_sub')}*")
                
                dc1, dc2 = st.columns(2)
                with dc1:
                    st.markdown(f"**🌾 {t('harvest_label')}:** {c_crop} · {c_qty:,.0f} kg (Grade {c_grade}) — #{c_lot_id}")
                    st.markdown(f"**👨‍🌾 {t('farmer_label')}:** {c_farmer_name} ({c_farmer_loc}, {c_farmer_dist})")
                    st.markdown(f"**🚚 {t('delivery_label')}:** {c_farmer_loc} ➔ {buyer_loc} ({c_distance:.0f} km)")
                with dc2:
                    st.markdown(f"**💰 {t('price_label')}:** ₹{c_price:.2f}/kg")
                    st.markdown(f"**💵 {t('potential_procurement_val')}:** ₹{c_total_val:,.0f}")
                    st.markdown(f"**🚚 {t('estimated_freight_label')}:** ₹{c_freight:,.0f}")

                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                btn_d1, btn_d2 = st.columns(2)
                with btn_d1:
                    if st.button(f"🤝 {t('btn_confirm_procurement_order')}", type="primary", use_container_width=True, key="btn_confirm_buyer_deal"):
                        dup_check = check_existing_active_order_for_produce(c_lot_id)
                        if dup_check:
                            st.session_state.buyer_confirming_lot_id = c_lot_id
                            st.rerun()
                        else:
                            new_tx = create_transaction(
                                farmer_id=c_farmer_id,
                                buyer_id=selected_buyer_id,
                                produce_id=c_lot_id,
                                quantity_kg=c_qty,
                                price_per_kg=c_price,
                                status="Order Placed",
                            )
                            st.session_state.buyer_confirming_lot_id = None
                            st.session_state.buyer_last_created_tx = {
                                "order_id": new_tx["transaction_id"],
                                "farmer_name": c_farmer_name,
                                "crop": c_crop,
                                "quantity_kg": c_qty,
                                "price_per_kg": c_price,
                                "total_value": c_total_val,
                            }
                            st.rerun()
                with btn_d2:
                    if st.button(f"✕ {t('btn_cancel_deal')}", use_container_width=True, key="btn_cancel_buyer_deal"):
                        st.session_state.buyer_confirming_lot_id = None
                        st.rerun()
            st.divider()

# Success State Card
if st.session_state.get("buyer_last_created_tx"):
    last_tx = st.session_state.buyer_last_created_tx
    with st.container(border=True):
        st.success(f"✓ **{t('order_created_title')} — #{last_tx['order_id']}**")
        st.markdown(t("order_initiated_success_desc"))
        
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown(f"**📋 {t('order_id_label')}:** #{last_tx['order_id']}")
            st.markdown(f"**👨‍🌾 {t('farmer_label')}:** {last_tx['farmer_name']}")
            st.markdown(f"**🌾 {t('produce_label')}:** {last_tx['crop']}")
        with sc2:
            st.markdown(f"**⚖️ {t('quantity_label')}:** {last_tx['quantity_kg']:,.0f} kg")
            st.markdown(f"**💰 {t('price_label')}:** ₹{last_tx['price_per_kg']:.2f}/kg")
            st.markdown(f"**💵 {t('total_value_label')}:** ₹{last_tx['total_value']:,.0f}")

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        if st.button(f"✕ {t('close')}", use_container_width=True, key="btn_close_buyer_tx_success"):
            st.session_state.buyer_last_created_tx = None
            st.rerun()
    st.divider()

# ============================================================
# 8. AVAILABLE PRODUCE & AI MATCHING ENGINE
# ============================================================

st.subheader(f"🌾 {t('matched_produce_title')}")
st.caption(f"{t('available_matches_label')}: **{buyer_crop}** ({t('min_grade_label', grade=buyer_min_qual)} · {t('max_budget_price')}: ₹{buyer_max_price:.2f}/kg)")

# Mandi benchmark lookup from Government data.gov.in AGMARKNET API
mandi_bench = get_mandi_market_benchmark(commodity=buyer_crop, district=buyer_district, state="Maharashtra")

# Resolve regional demand dataset hierarchy
regional_demand_df, demand_src_label = get_regional_demand_series(
    district=buyer_district,
    crop=buyer_crop,
    demand_df=demand_df,
    transactions_df=transactions_df,
    produce_df=produce_df,
)

if regional_demand_df is not None:
    demand_fc = forecast_demand(demand_df=regional_demand_df, district=buyer_district, crop=buyer_crop, forecast_days=3)
    if demand_fc is not None:
        demand_fc["demand_source"] = demand_src_label
else:
    demand_fc = None

forecast_kg = demand_fc["forecast_demand_kg"] if demand_fc is not None else None

matched_lots = []
for _, p_row in available_produce.iterrows():
    if str(p_row["crop"]).lower() != buyer_crop.lower():
        continue
    
    dist_val = get_distance(p_row["district"], buyer_district)
    m_score = calculate_match_score(
        quantity=float(p_row["quantity_kg"]),
        buyer_quantity=buyer_req_qty,
        farmer_quality=p_row["quality_grade"],
        buyer_quality=buyer_min_qual,
        farmer_price=float(p_row["expected_price_per_kg"]),
        buyer_price=buyer_max_price,
        distance=dist_val,
        forecast_demand=forecast_kg,
        farmer_date=p_row["available_date"],
        buyer_date=buyer_req_date,
    )
    
    # Farmer name lookup
    f_info = farmers_df[farmers_df["farmer_id"].astype(str) == str(p_row["farmer_id"])]
    f_name = f_info.iloc[0]["name"] if not f_info.empty else f"Farmer {p_row['farmer_id']}"
    
    matched_lots.append({
        "produce_id": p_row["produce_id"],
        "farmer_id": p_row["farmer_id"],
        "farmer_name": f_name,
        "crop": p_row["crop"],
        "quantity_kg": float(p_row["quantity_kg"]),
        "quality_grade": p_row["quality_grade"],
        "expected_price_per_kg": float(p_row["expected_price_per_kg"]),
        "location": p_row["location"],
        "district": p_row["district"],
        "available_date": p_row["available_date"],
        "distance_km": dist_val,
        "match_score": m_score,
    })

matched_df = pd.DataFrame(matched_lots)
if not matched_df.empty:
    matched_df = matched_df.sort_values("match_score", ascending=False).reset_index(drop=True)

# Render Matches or Empty State
if matched_df.empty:
    with st.container(border=True):
        st.warning(f"⚠️ **{t('no_suitable_produce_title')}**")
        st.markdown(f"*{t('no_suitable_produce_desc')}*")
        st.caption(f"Required: **{buyer_crop}** · {buyer_req_qty:,.0f} kg · Grade {buyer_min_qual} · Max ₹{buyer_max_price:.2f}/kg")
        
        btn_es1, btn_es2 = st.columns(2)
        with btn_es1:
            if st.button(f"📝 {t('btn_edit_requirement')}", type="primary", use_container_width=True, key="btn_no_match_edit_req"):
                st.switch_page("pages/buyer_requirements.py")
        with btn_es2:
            if st.button(f"🏪 {t('btn_view_digital_mandi')}", use_container_width=True, key="btn_no_match_mandi"):
                st.switch_page("pages/digital_mandi.py")
else:
    # 8A. DOMINANT CARD: TOP RECOMMENDED FARMER LOT
    top_lot = matched_df.iloc[0]
    top_pid = str(top_lot["produce_id"])
    top_crop = str(top_lot["crop"])
    top_qty = float(top_lot["quantity_kg"])
    top_grade = str(top_lot["quality_grade"])
    top_price = float(top_lot["expected_price_per_kg"])
    top_farmer = str(top_lot["farmer_name"])
    top_loc = str(top_lot["location"])
    top_dist = str(top_lot["district"])
    top_score = int(float(top_lot["match_score"]))
    top_dist_km = float(top_lot["distance_km"])
    top_total_val = top_qty * top_price
    
    top_card_html = f"""
    <div style="background: linear-gradient(145deg, #163E2B 0%, #1E5128 55%, #163E2B 100%); color: #FFFFFF; border-radius: 20px; padding: 24px 28px; margin-bottom: 1.2rem; box-shadow: 0 14px 34px rgba(22, 62, 43, 0.22); border: 1.5px solid rgba(217, 119, 6, 0.4); position: relative; overflow: hidden;">
        <div style="position: absolute; right: -30px; top: -30px; width: 150px; height: 150px; background: radial-gradient(circle, rgba(217, 119, 6, 0.25) 0%, transparent 70%); border-radius: 50%; pointer-events: none;"></div>
        
        <div style="position: relative; z-index: 1;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                <span style="font-size: 0.74rem; font-weight: 900; letter-spacing: 0.08em; text-transform: uppercase; background: linear-gradient(135deg, #E5A010 0%, #D97706 100%); color: #FFFFFF; padding: 4px 14px; border-radius: 20px;">
                    {t('best_available_opportunity_title')}
                </span>
                <span style="font-size: 0.80rem; font-weight: 800; color: #86EFAC; background: rgba(0,0,0,0.25); padding: 4px 12px; border-radius: 12px; border: 1px solid rgba(134,239,172,0.3);">
                    ✦ {top_score}% MATCH · {t('recommended_match_badge')}
                </span>
            </div>

            <div style="font-size: 1.7rem; font-weight: 900; color: #FFFFFF; margin-bottom: 4px;">
                {crop_icons.get(top_crop.lower(), '🌱')} {top_crop.upper()} · GRADE {top_grade}
            </div>

            <div style="font-size: 1.0rem; font-weight: 600; color: #D7B982; margin-bottom: 12px;">
                👨‍🌾 {top_farmer} · 📍 {top_loc}, {top_dist} ({top_dist_km:.0f} km ➔ {buyer_loc})
            </div>

            <div style="display: flex; align-items: baseline; gap: 18px; flex-wrap: wrap; margin-bottom: 12px;">
                <div style="font-size: 2.0rem; font-weight: 900; color: #F7E9B7;">
                    ₹{top_price:.2f} <span style="font-size: 0.95rem; font-weight: 600; color: #E5DFD3;">/ kg</span>
                </div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #E5DFD3;">
                    {t('potential_procurement_val')}: <strong style="color: #FFFFFF;">₹{top_total_val:,.0f}</strong> ({top_qty:,.0f} kg)
                </div>
            </div>

            <div style="display: flex; gap: 20px; flex-wrap: wrap; font-size: 0.88rem; color: #E5DFD3; border-top: 1px solid rgba(255,255,255,0.14); padding-top: 10px;">
                <span>🚚 {t('estimated_distance_label')}: <strong>{top_dist_km:.0f} km</strong></span>
                <span>📅 {t('available_date')}: <strong>{top_lot['available_date']}</strong></span>
                <span>🏷️ Lot ID: <strong>#{top_pid}</strong></span>
            </div>
        </div>
    </div>
    """
    render_html(top_card_html)

    # Dominant Card Actions
    btn_col1, btn_col2, btn_col3 = st.columns([1.8, 1.2, 1.2])
    with btn_col1:
        if st.button(f"🤝 {t('btn_accept_procurement')} →", type="primary", use_container_width=True, key=f"btn_accept_top_{top_pid}"):
            st.session_state.buyer_confirming_lot_id = top_pid
            st.rerun()
    with btn_col2:
        btn_passport_label = t("btn_hide_lot") if st.session_state.buyer_show_passport_lot_id == top_pid else t("btn_view_lot")
        if st.button(f"👁 {btn_passport_label}", use_container_width=True, key=f"btn_pass_top_{top_pid}"):
            st.session_state.buyer_show_passport_lot_id = None if st.session_state.buyer_show_passport_lot_id == top_pid else top_pid
            st.rerun()
    with btn_col3:
        btn_route_label = t("btn_hide_route") if st.session_state.buyer_show_route_lot_id == top_pid else t("btn_view_route")
        if st.button(f"🗺️ {btn_route_label}", use_container_width=True, key=f"btn_route_top_{top_pid}"):
            st.session_state.buyer_show_route_lot_id = None if st.session_state.buyer_show_route_lot_id == top_pid else top_pid
            st.rerun()

    # Conditional Farm Passport Drawer
    if st.session_state.get("buyer_show_passport_lot_id") == top_pid:
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        render_farm_passport(
            farmer_name=top_farmer,
            location=f"{top_loc}, {top_dist}",
            crop=top_crop,
            harvest_date=str(top_lot["available_date"]),
            grade=top_grade,
            match_score=top_score,
            logistics_route=f"{top_loc} ➔ {buyer_loc} Hub",
        )

    # Conditional Route Map Drawer
    if st.session_state.get("buyer_show_route_lot_id") == top_pid:
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        top_freight = base_freight + (top_dist_km * cost_per_km)
        display_optimized_route_map(
            route=[top_loc, buyer_loc],
            farmer_names={top_loc: top_farmer},
            buyer_name=buyer_name,
            crop=top_crop,
            total_distance_km=top_dist_km,
            total_load_kg=top_qty,
            logistics_cost=top_freight,
        )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 8B. BUYER INTELLIGENCE SECTION (DECISION-SUPPORT ENGINE)
    top_intel = calculate_buyer_intelligence(
        produce_lot=top_lot,
        buyer_requirement=buyer_row,
        mandi_benchmark=mandi_bench,
        demand_forecast=demand_fc,
        logistics=selected_logistics,
        custom_distance_km=top_dist_km,
        match_score=top_score,
    )

    with st.container(border=True):
        st.subheader(f"🧠 {t('buyer_intelligence_title', default='Buyer Intelligence')} ({top_crop} · {top_farmer})")
        st.caption("Factual lot procurement evaluation vs. requirement specification & live mandi benchmark")

        # Top Quality Intelligence
        top_quality_intel = calculate_quality_intelligence(
            quality_grade=top_grade,
            minimum_quality=buyer_min_qual,
            crop=top_crop
        )

        # 3 Top Telemetry Cards
        bi_col1, bi_col2, bi_col3 = st.columns(3)
        with bi_col1:
            st.metric(
                label="Match Score",
                value=f"{top_intel['match_score']}%",
                help="Algorithmic compatibility score",
            )
            st.caption(f"🎯 Alignment: {'Strong' if top_intel['match_score'] >= 85 else 'Moderate'}")

        with bi_col2:
            st.metric(
                label="Quantity Fit",
                value=f"{top_intel['fill_percentage']:.1f}%",
                help="Percentage of required volume covered by this lot (capped at 100%)",
            )
            st.caption(f"⚖️ {top_intel['available_quantity_kg']:,.0f} / {top_intel['buyer_required_quantity_kg']:,.0f} kg")

        with bi_col3:
            st.metric(
                label="Quality Standard",
                value=f"Grade {top_intel['quality_grade']}",
                help="Farmer lot produce quality classification",
            )
            st.caption(f"📋 Required: Grade {top_intel['buyer_min_quality']} ({top_quality_intel['quality_status']})")

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # 3 Structured Intelligence Detail Columns
        b_c1, b_c2, b_c3 = st.columns(3)
        
        with b_c1:
            st.markdown("**👨‍🌾 Farmer & Location**")
            st.markdown(f"**Farmer:** `{top_intel['farmer_name']}`")
            st.markdown(f"**Location:** `{top_intel['farmer_location']}`")
            st.markdown(f"**Quality Status:** `{top_quality_intel['quality_status']}`")
            st.caption(f"Lot #{top_intel['produce_id']} · Available: {top_lot.get('available_date', 'Immediate')}")

        with b_c2:
            st.markdown("**💰 Pricing vs. Mandi Benchmark**")
            st.markdown(f"**Farmer Price:** `₹{top_intel['farmer_expected_price_per_kg']:.2f}/kg`")
            if top_intel['mandi_modal_price_per_kg'] is not None:
                p_diff = top_intel['price_difference_vs_mandi']
                sign = "+" if p_diff and p_diff >= 0 else ""
                diff_str = f"{sign}₹{p_diff:.2f}/kg" if p_diff is not None else ""
                st.markdown(f"**Live Mandi:** `₹{top_intel['mandi_modal_price_per_kg']:.2f}/kg` ({diff_str})")
                st.caption(f"🏷️ *{top_intel['market_context']}* ({top_intel['mandi_market']})")
            else:
                st.caption("Live mandi benchmark unavailable")

        with b_c3:
            st.markdown("**🚚 Logistics & Demand Outlook**")
            st.markdown(f"**Route:** `{top_intel['distance_km']:.0f} km` (Est. Freight: ₹{top_intel['logistics_cost']:,.0f})")
            if top_intel['demand_signal'] != "Unavailable":
                d_pct = top_intel['demand_percentage_change']
                sign_d = "+" if (d_pct or 0) >= 0 else ""
                pct_d_str = f" ({sign_d}{d_pct:.1f}%)" if d_pct is not None else ""
                st.markdown(f"**Demand Signal:** `{top_intel['demand_signal']}{pct_d_str}`")
                st.caption(f"Source: *{top_intel['demand_source']}*")
            else:
                st.markdown("**Demand Signal:** `Unavailable`")
                st.caption("Insufficient regional observations")

        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

        # Factual Non-Speculative Explanation
        st.info(f"💡 **Procurement Intelligence:** {top_intel['explanation']}")

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 8C. WHY THIS MATCH? (6 FACTOR TRANSPARENT BREAKDOWN)
    st.subheader(f"💡 {t('why_this_match_title')}")
    
    why_html = f"""
    <div style="background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border: 1px solid rgba(22, 62, 43, 0.12); border-radius: 14px; padding: 18px 20px; margin-bottom: 1.2rem; box-shadow: 0 4px 14px rgba(22, 62, 43, 0.04);">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; font-size: 0.88rem; color: #163E2B;">
            <div>✓ <strong>{t('factor_qty_match')}:</strong> {top_qty:,.0f} kg ({int(top_qty/buyer_req_qty*100)}% of required {buyer_req_qty:,.0f} kg)</div>
            <div>✓ <strong>{t('factor_qual_match')}:</strong> Grade {top_grade} meets required Grade {buyer_min_qual} ({top_quality_intel['quality_status']})</div>
            <div>✓ <strong>{t('factor_price_budget')}:</strong> ₹{top_price:.2f}/kg is within budget ceiling ₹{buyer_max_price:.2f}/kg</div>
            <div>✓ <strong>{t('factor_distance_route')}:</strong> {top_dist_km:.0f} km direct route {top_dist} ➔ {buyer_district}</div>
            <div>✓ <strong>{t('factor_demand_timing')}:</strong> Available {top_lot['available_date']} aligns with requirement date</div>
            <div>✓ <strong>{t('zero_middleman_badge')}:</strong> Direct procurement from verified producer</div>
        </div>
    </div>
    """
    render_html(why_html)

    # 8D. OTHER MATCHING FARMER LOTS (IF MULTIPLE)
    if len(matched_df) > 1:
        st.subheader(f"🤝 {t('available_buyer_matches_title')}")
        st.caption(f"{len(matched_df) - 1} other farmer lot matches available")

        for idx, m_lot in matched_df.iloc[1:].iterrows():
            m_pid = str(m_lot["produce_id"])
            m_farmer = str(m_lot["farmer_name"])
            m_loc = str(m_lot["location"])
            m_price = float(m_lot["expected_price_per_kg"])
            m_qty = float(m_lot["quantity_kg"])
            m_grade = str(m_lot["quality_grade"])
            m_score = int(float(m_lot["match_score"]))
            m_dist = float(m_lot["distance_km"])
            m_total = m_qty * m_price

            m_intel = calculate_buyer_intelligence(
                produce_lot=m_lot,
                buyer_requirement=buyer_row,
                mandi_benchmark=mandi_bench,
                demand_forecast=demand_fc,
                logistics=selected_logistics,
                custom_distance_km=m_dist,
                match_score=m_score,
            )

            m_qual_intel = calculate_quality_intelligence(
                quality_grade=m_grade,
                minimum_quality=buyer_min_qual,
                crop=m_lot["crop"],
            )

            with st.container(border=True):
                mc1, mc2, mc3 = st.columns([2.5, 1.5, 1.2])
                with mc1:
                    st.markdown(f"**🌱 {m_lot['crop']} · Grade {m_grade}** (#{m_pid})")
                    st.caption(f"👨‍🌾 {m_farmer} · 📍 {m_loc}, {m_lot['district']} ({m_dist:.0f} km) · 📅 {m_lot['available_date']}")
                    st.caption(f"📊 Fit: **{m_intel['fill_percentage']:.0f}%** · Quality: **Grade {m_grade}** (Req: Grade {buyer_min_qual} · *{m_qual_intel['quality_status']}*) · Context: *{m_intel['market_context']}*")
                with mc2:
                    st.markdown(f"💰 **₹{m_price:.2f}/kg** · ⭐ **{m_score}% Match**")
                    st.caption(f"{t('potential_procurement_val')}: ₹{m_total:,.0f} ({m_qty:,.0f} kg)")
                with mc3:
                    if st.button(f"🤝 {t('btn_accept_procurement')}", key=f"btn_accept_other_{m_pid}_{idx}", type="primary", use_container_width=True):
                        st.session_state.buyer_confirming_lot_id = m_pid
                        st.rerun()

st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

# ============================================================
# 9. INCOMING & ACTIVE ORDERS PIPELINE
# ============================================================

st.subheader(f"📦 {t('incoming_orders_pipeline_title')}")

if buyer_txs.empty:
    render_empty_state(
        t("no_active_orders_buyer_title"),
        t("no_active_orders_buyer_desc"),
        t("no_active_orders_buyer_action"),
    )
else:
    for _, tx in buyer_txs.iterrows():
        tx_id = tx["transaction_id"]
        status = str(tx["status"])
        farmer_id = str(tx["farmer_id"])
        produce_id = str(tx.get("produce_id", ""))
        qty = float(tx.get("quantity_kg", 0))
        rate = float(tx.get("price_per_kg", 0))
        total_val = float(tx.get("total_value", qty * rate))
        tx_date = str(tx.get("date", ""))
        
        # Farmer name lookup
        f_rec = farmers_df[farmers_df["farmer_id"].astype(str) == farmer_id]
        f_name_label = f_rec.iloc[0]["name"] if not f_rec.empty else f"Farmer {farmer_id}"
        
        # Produce name lookup
        p_rec = produce_df[produce_df["produce_id"].astype(str) == produce_id]
        p_crop_name = p_rec.iloc[0]["crop"] if not p_rec.empty else "Produce"
        p_grade = p_rec.iloc[0]["quality_grade"] if not p_rec.empty else "A"

        status_color = "#E8B83D" if status == "Order Placed" else (
            "#176536" if status in ["Confirmed", "Completed"] else (
                "#1952B3" if status == "In Transit" else (
                    "#5B2B82" if status == "Delivered" else "#9E4932"
                )
            )
        )
        status_key = f"status_{status.lower().replace(' ', '_')}"
        status_text = t(status_key)

        with st.container(border=True):
            col_l, col_m, col_r = st.columns([2.5, 2, 1.5])
            with col_l:
                st.markdown(f"### 🤝 {t('deal_number', deal_id=tx_id)}")
                st.write(f"**{t('farmer_label')}:** {f_name_label} (#{farmer_id})")
                st.write(f"**{t('produce_lot')}:** {crop_icons.get(p_crop_name.lower(), '🌱')} {p_crop_name} (Grade {p_grade}) — #{produce_id}")
            with col_m:
                st.write(f"**{t('volume')}:** {qty:,.0f} kg @ ₹{rate:.2f}/kg")
                st.write(f"**{t('total_deal_val')}:** **₹{total_val:,.0f}**")
                st.markdown(f"{t('status')}: <span style='color:{status_color}; font-weight:800;'>● {status_text}</span>", unsafe_allow_html=True)
                st.caption(f"📅 {t('date')}: {tx_date}")
            with col_r:
                if status == "Order Placed":
                    if st.button(f"✅ {t('btn_confirm_order')}", key=f"b_conf_{tx_id}", type="primary", use_container_width=True):
                        update_transaction_status(tx_id, "Confirmed")
                        st.rerun()
                    if st.button(f"❌ {t('btn_reject')}", key=f"b_rej_{tx_id}", use_container_width=True):
                        update_transaction_status(tx_id, "Rejected")
                        st.rerun()
                elif status == "Confirmed":
                    if st.button(f"🚚 {t('btn_mark_in_transit')}", key=f"b_trans_{tx_id}", type="primary", use_container_width=True):
                        update_transaction_status(tx_id, "In Transit")
                        st.rerun()
                elif status == "In Transit":
                    if st.button(f"📍 {t('btn_mark_delivered')}", key=f"b_del_{tx_id}", type="primary", use_container_width=True):
                        update_transaction_status(tx_id, "Delivered")
                        st.rerun()
                elif status == "Delivered":
                    if st.button(f"🎉 {t('btn_complete_deal')}", key=f"b_comp_{tx_id}", type="primary", use_container_width=True):
                        update_transaction_status(tx_id, "Completed")
                        st.rerun()
                elif status == "Completed":
                    st.markdown(f"<span style='color:#176536; font-weight:700;'>✓ {t('payment_settled')}</span>", unsafe_allow_html=True)

st.divider()

# ============================================================
# 10. PROCUREMENT TRANSACTION HISTORY
# ============================================================

st.subheader(f"📜 {t('procurement_tx_history')}")

if buyer_txs.empty:
    st.info(t("no_tx_history"))
else:
    display_history = buyer_txs[[
        "transaction_id", "farmer_id", "produce_id", "quantity_kg", "price_per_kg", "total_value", "status", "date"
    ]].copy()
    display_history.columns = [
        t("col_transaction_id"),
        t("col_farmer_id"),
        t("col_produce_lot"),
        t("col_quantity_kg"),
        t("col_price_kg"),
        t("col_order_val"),
        t("col_status"),
        t("col_date"),
    ]
    st.dataframe(display_history, use_container_width=True, hide_index=True)

st.caption(f"ℹ️ {t('buyer_footer_caption')}")