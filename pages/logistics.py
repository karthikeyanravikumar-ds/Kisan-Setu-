"""
Logistics & Setu Load Fulfillment Dashboard | Kisan Setu
Theme: 'Bharat, Reimagined'

Operational Logistics Hub answering:
1. What deliveries are active?
2. Where do they need to go?
3. What is the route?
4. What vehicle/load is involved?
5. What is the current delivery status?

Integrates:
- Section 1: Logistics Overview (Active, Assigned, Pending Pickups, In Transit, Delivered)
- Section 2: Available Logistics Partners (from data/logistics_partners.csv)
- Section 3: Assign Logistics Partner (with capacity, service corridor, and availability filtering)
- Section 4: Delivery Detail & Visual Logistics Status Tracker (Requested -> Assigned -> Pickup Scheduled -> In Transit -> Delivered)
- Section 5: Multi-Stop OR-Tools Route Optimizer & Mapping
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import folium
from streamlit_folium import st_folium

from utils.data_loader import (
    load_logistics,
    load_produce,
    load_buyers,
    load_farmers,
    load_transactions,
)
from utils.consumer_orders import load_consumer_orders
from utils.transactions import update_transaction_status
from logistics.route_optimizer import optimize_route
from logistics.partner_manager import (
    load_logistics_partners,
    match_logistics_partners,
    assign_partner_to_transaction,
    update_partner_assignment_status,
    get_partner_for_transaction,
    load_partner_assignments,
    render_logistics_status_stepper_html,
    PROTOTYPE_NETWORK_LABEL,
    NO_THIRD_PARTY_NOTE,
    EXPLANATORY_NOTE,
)
from maps.route_map import display_optimized_route_map, get_coordinates
from ai.matching import get_distance
from utils.translations import t, get_current_language

from ui.theme import inject_custom_theme
from ui.setu_components import (
    render_brand_header,
    render_bharat_market_pulse,
    render_empty_state,
    render_html,
)

# =========================================================
# 1. THEME & INITIALIZATION
# =========================================================

inject_custom_theme()
language = get_current_language()

# Load Core Datasets
logistics_df = load_logistics()
produce_df = load_produce()
buyers_df = load_buyers()
farmers_df = load_farmers()
transactions_df = load_transactions()
consumer_orders_df = load_consumer_orders()
partners_df = load_logistics_partners()
assignments_df = load_partner_assignments()

# State Management
if "logistics_selected_delivery_id" not in st.session_state:
    st.session_state.logistics_selected_delivery_id = None

if "logistics_show_route_map" not in st.session_state:
    st.session_state.logistics_show_route_map = False

# Crop Icons
crop_icons = {
    "onion": "🧅",
    "tomato": "🍅",
    "potato": "🥔",
    "wheat": "🌾",
    "banana": "🍌",
    "ginger": "🫚",
    "rice": "🍚",
}

# =========================================================
# 2. BRAND HEADER & MARKET PULSE
# =========================================================

render_bharat_market_pulse()

render_brand_header(
    title=t("logistics_hub_header"),
    subtitle=t("logistics_hub_subtitle"),
    badge=t("badge_infra_active"),
)

# Explanatory Card & Disclaimers
render_html(f"""
<div style="background: rgba(22, 62, 43, 0.05); border: 1px solid rgba(22, 62, 43, 0.18); border-left: 4px solid #163E2B; border-radius: 10px; padding: 14px 18px; margin-bottom: 1.2rem;">
    <div style="font-weight: 800; color: #163E2B; font-size: 0.95rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px;">
        <span>🚛 Logistics Partner Orchestration Network</span>
        <span style="font-size: 0.74rem; background: #163E2B; color: #FFFFFF; padding: 2px 8px; border-radius: 6px; font-weight: 700;">{PROTOTYPE_NETWORK_LABEL}</span>
    </div>
    <div style="font-size: 0.86rem; color: #2D3A32; margin-top: 6px; line-height: 1.45;">
        {EXPLANATORY_NOTE}
    </div>
    <div style="font-size: 0.76rem; color: #526058; margin-top: 6px; font-style: italic;">
        ⚠️ {NO_THIRD_PARTY_NOTE}
    </div>
</div>
""")

st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

# =========================================================
# SECTION 1 — LOGISTICS OVERVIEW
# =========================================================

st.subheader(f"📊 Section 1 — Logistics Overview")
st.caption("Real-time telemetry across platform delivery transactions and fleet fulfillment")

# Real Metrics Calculations
active_deliveries_cnt = len(transactions_df[transactions_df["status"].astype(str).isin(["Order Placed", "Confirmed", "In Transit"])])
assigned_partners_cnt = len(assignments_df[assignments_df["status"].astype(str).isin(["Assigned", "Pickup Scheduled", "In Transit"])]) if not assignments_df.empty else 0
pending_pickups_cnt = len(assignments_df[assignments_df["status"].astype(str).isin(["Requested", "Assigned", "Pickup Scheduled"])]) if not assignments_df.empty else 0
in_transit_cnt = len(transactions_df[transactions_df["status"].astype(str) == "In Transit"])
delivered_cnt = len(transactions_df[transactions_df["status"].astype(str).isin(["Delivered", "Completed"])])

ov1, ov2, ov3, ov4, ov5 = st.columns(5)
ov1.metric(f"📦 Active Deliveries", active_deliveries_cnt)
ov2.metric(f"🤝 Assigned Partners", assigned_partners_cnt)
ov3.metric(f"⏳ Pending Pickups", pending_pickups_cnt)
ov4.metric(f"🚚 In Transit", in_transit_cnt)
ov5.metric(f"✅ Delivered", delivered_cnt)

st.divider()

# =========================================================
# SECTION 2 — AVAILABLE LOGISTICS PARTNERS
# =========================================================

st.subheader(f"🚛 Section 2 — Available Logistics Partners")
st.caption(f"Verified regional fleet operators registered under {PROTOTYPE_NETWORK_LABEL}")

if partners_df.empty:
    st.info("No logistics partners registered.")
else:
    partner_cols = st.columns(min(3, len(partners_df)))
    for idx, p_row in partners_df.iterrows():
        col_target = partner_cols[idx % len(partner_cols)]
        p_id = str(p_row["partner_id"])
        p_name = str(p_row["partner_name"])
        v_type = str(p_row["vehicle_type"])
        cap_val = float(p_row.get("capacity_kg", 1000))
        cost_km = float(p_row.get("cost_per_km", 28.0))
        base_c = float(p_row.get("base_cost", 500.0))
        avail = str(p_row.get("availability", "Available"))
        rating = float(p_row.get("rating", 4.8))
        service_area = str(p_row.get("service_regions", "Maharashtra"))
        base_loc = str(p_row.get("base_location", "Nashik"))

        avail_badge = "🟢 Available" if avail.lower() == "available" else "🔴 Busy"

        with col_target:
            st.markdown(
                f"""
                <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-top: 4px solid #163E2B; border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(24,32,27,0.03);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 800; color: #163E2B; font-size: 0.95rem;">{p_name}</span>
                        <span style="font-size: 0.72rem; font-weight: 700;">{avail_badge}</span>
                    </div>
                    <div style="font-size: 0.82rem; color: #526058; margin: 4px 0;">
                        <b>Vehicle:</b> {v_type} · <b>Cap:</b> {cap_val:,.0f} kg
                    </div>
                    <div style="font-size: 0.80rem; color: #68756C;">
                        📍 <b>Base:</b> {base_loc} · <b>Corridors:</b> {service_area}
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px; padding-top: 6px; border-top: 1px dashed #E5DFD3; font-size: 0.82rem;">
                        <span>💰 <b>₹{cost_km:.0f}/km</b> + ₹{base_c:.0f} base</span>
                        <span>⭐ <b>{rating}</b></span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.divider()

# =========================================================
# SECTION 3 — ASSIGN LOGISTICS PARTNER
# =========================================================

st.subheader(f"🤝 Section 3 — Assign Logistics Partner")
st.caption("Match candidate transactions with eligible vehicle capacity, corridor coverage, and transparent freight rates")

if transactions_df.empty:
    st.info("No transactions available for partner assignment.")
else:
    # Transaction selection options
    tx_options = transactions_df["transaction_id"].astype(str).tolist()
    
    # Format transaction display
    def format_tx_opt(tx_val):
        t_row = transactions_df[transactions_df["transaction_id"].astype(str) == str(tx_val)]
        if t_row.empty:
            return tx_val
        tr = t_row.iloc[0]
        p_row = produce_df[produce_df["produce_id"].astype(str) == str(tr["produce_id"])]
        crop_val = p_row.iloc[0]["crop"] if not p_row.empty else "Produce"
        return f"Transaction #{tx_val} · {crop_val} ({float(tr['quantity_kg']):,.0f} kg) · Status: {tr['status']}"

    default_tx_idx = 0
    if st.session_state.get("logistics_selected_delivery_id") in tx_options:
        default_tx_idx = tx_options.index(st.session_state.logistics_selected_delivery_id)

    selected_tx_id = st.selectbox(
        "Select Transaction / Order to Assign Partner:",
        tx_options,
        index=default_tx_idx,
        format_func=format_tx_opt,
        key="sel_assign_tx_dropdown",
    )

    # Sync selection with detail view
    st.session_state.logistics_selected_delivery_id = selected_tx_id

    # Retrieve transaction metadata
    curr_tx = transactions_df[transactions_df["transaction_id"].astype(str) == str(selected_tx_id)].iloc[0]
    t_status = str(curr_tx["status"])
    t_farmer_id = str(curr_tx["farmer_id"])
    t_buyer_id = str(curr_tx["buyer_id"])
    t_produce_id = str(curr_tx["produce_id"])
    t_qty = float(curr_tx.get("quantity_kg", 500))
    t_rate = float(curr_tx.get("price_per_kg", 30))
    t_total = float(curr_tx.get("total_value", t_qty * t_rate))

    # Lookups for origin & destination
    f_match = farmers_df[farmers_df["farmer_id"].astype(str) == t_farmer_id]
    f_name = f_match.iloc[0]["name"] if not f_match.empty else f"Farmer {t_farmer_id}"
    f_loc = f_match.iloc[0]["village"] if not f_match.empty else "Niphad"
    f_dist = f_match.iloc[0]["district"] if not f_match.empty else "Nashik"

    b_match = buyers_df[buyers_df["buyer_id"].astype(str) == t_buyer_id]
    b_name = b_match.iloc[0]["name"] if not b_match.empty else f"Buyer {t_buyer_id}"
    b_loc = b_match.iloc[0]["location"] if not b_match.empty else "Pune"
    b_dist = b_match.iloc[0]["district"] if not b_match.empty else "Pune"

    p_match = produce_df[produce_df["produce_id"].astype(str) == t_produce_id]
    p_crop = str(p_match.iloc[0]["crop"]) if not p_match.empty else "Onion"
    p_grade = str(p_match.iloc[0]["quality_grade"]) if not p_match.empty else "A"

    calculated_distance_km = float(get_distance(f_dist, b_dist))

    # Display Order Requirement Summary Box
    with st.container(border=True):
        st.markdown(f"**📦 Requirement Details for #{selected_tx_id}:**")
        req_col1, req_col2, req_col3, req_col4 = st.columns(4)
        req_col1.markdown(f"**🌾 Crop:** {crop_icons.get(p_crop.lower(), '🌱')} {p_crop} (Grade {p_grade})")
        req_col2.markdown(f"**⚖️ Quantity:** {t_qty:,.0f} kg")
        req_col3.markdown(f"**📍 Origin:** {f_name} ({f_loc}, {f_dist})")
        req_col4.markdown(f"**🏢 Destination:** {b_name} ({b_loc}, {b_dist})")

        dist_col1, dist_col2 = st.columns(2)
        dist_col1.markdown(f"**🚚 Calculated Distance:** `{calculated_distance_km:.0f} km` ({f_dist} ➔ {b_dist})")
        dist_col2.markdown(f"**💰 Order Value:** ₹{t_total:,.0f} (@ ₹{t_rate:.2f}/kg)")

    # Check Existing Partner Assignment
    current_partner = get_partner_for_transaction(selected_tx_id)
    if current_partner:
        st.markdown(
            f"""
            <div style="background: rgba(22, 62, 43, 0.08); border: 1.5px solid #163E2B; border-radius: 10px; padding: 14px 18px; margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px;">
                    <span style="font-weight: 800; color: #163E2B; font-size: 1.0rem;">🤝 Current Assigned Partner: {current_partner.get('partner_name')}</span>
                    <span style="font-size: 0.8rem; background: #163E2B; color: #FFFFFF; padding: 3px 10px; border-radius: 6px; font-weight: 700;">Status: {current_partner.get('status')}</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 8px; margin-top: 8px; font-size: 0.86rem;">
                    <div>🚛 <b>Vehicle:</b> {current_partner.get('vehicle', 'Mini Truck')}</div>
                    <div>💰 <b>Estimated Freight:</b> ₹{float(current_partner.get('estimated_freight', 0)):,.0f}</div>
                    <div>📍 <b>Pickup:</b> {current_partner.get('pickup_location')}</div>
                    <div>🏢 <b>Destination:</b> {current_partner.get('destination')}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Candidate Matching Filter
    matched_candidates = match_logistics_partners(
        required_quantity_kg=t_qty,
        origin=f_dist,
        destination=b_dist,
        only_available=True,
    )

    with st.expander("🔍 Match & Re-Assign Logistics Partner", expanded=(current_partner is None)):
        if not matched_candidates:
            st.warning(f"No available partner matches the required capacity ({t_qty:,.0f} kg) or corridor ({f_dist} ➔ {b_dist}).")
        else:
            st.caption("Only displaying verified partners with sufficient capacity, service corridor coverage, and 'Available' status:")
            for c_idx, cand in enumerate(matched_candidates):
                c_col1, c_col2, c_col3 = st.columns([2.5, 1.5, 1.2])
                with c_col1:
                    st.markdown(f"**🚛 {cand['partner_name']}** ({cand['vehicle_type']})")
                    st.caption(f"Cap: {cand['capacity_kg']:,.0f} kg ({cand['capacity_utilization_pct']:.0f}% load) · ⭐ {cand['rating']} · Base: {cand['base_location']}")
                with c_col2:
                    st.markdown(f"**₹{cand['estimated_freight']:,.0f}** freight")
                    st.caption(f"₹{cand['cost_per_km']:.0f}/km + Base ₹{cand['base_cost']:,.0f} (₹{cand['freight_per_kg']:.2f}/kg)")
                with c_col3:
                    if st.button("Assign Partner", key=f"btn_assign_partner_{selected_tx_id}_{cand['partner_id']}_{c_idx}", type="primary", use_container_width=True):
                        assign_partner_to_transaction(
                            partner_id=cand["partner_id"],
                            transaction_id=selected_tx_id,
                            pickup_location=f"{f_loc}, {f_dist}",
                            destination=f"{b_loc}, {b_dist}",
                            quantity_kg=t_qty,
                            estimated_freight=cand["estimated_freight"],
                            vehicle=cand["vehicle_type"],
                            status="Assigned",
                        )
                        st.success(f"Successfully assigned {cand['partner_name']} to #{selected_tx_id}!")
                        st.rerun()

st.divider()

# =========================================================
# SECTION 4 — DELIVERY DETAIL & LOGISTICS STATUS TRACKER
# =========================================================

st.subheader(f"🚚 Section 4 — Active Delivery Detail & Status Tracker")
st.caption(f"Lifecycle monitoring for Transaction #{selected_tx_id}")

active_assigned_partner = get_partner_for_transaction(selected_tx_id)
partner_status = active_assigned_partner.get("status", "Requested") if active_assigned_partner else "Requested"

# Visual Stepper Rendering
render_html(render_logistics_status_stepper_html(partner_status))

# Action Buttons for Lifecycle Status Transitions
with st.container(border=True):
    st.markdown(f"**⚡ Fulfillment Lifecycle Actions for #{selected_tx_id}:**")
    act1, act2, act3, act4, act5 = st.columns(5)

    with act1:
        if st.button("📋 Request", key=f"btn_st_req_{selected_tx_id}", use_container_width=True):
            update_partner_assignment_status(selected_tx_id, "Requested")
            st.rerun()
    with act2:
        if st.button("🤝 Assign", key=f"btn_st_ass_{selected_tx_id}", use_container_width=True):
            update_partner_assignment_status(selected_tx_id, "Assigned")
            st.rerun()
    with act3:
        if st.button("📦 Schedule Pickup", key=f"btn_st_sch_{selected_tx_id}", use_container_width=True):
            update_partner_assignment_status(selected_tx_id, "Pickup Scheduled")
            st.rerun()
    with act4:
        if st.button("🚚 Dispatch / Transit", key=f"btn_st_trans_{selected_tx_id}", use_container_width=True, type="primary" if partner_status == "Pickup Scheduled" else "secondary"):
            update_partner_assignment_status(selected_tx_id, "In Transit")
            update_transaction_status(selected_tx_id, "In Transit")
            st.rerun()
    with act5:
        if st.button("✅ Mark Delivered", key=f"btn_st_deliv_{selected_tx_id}", use_container_width=True, type="primary" if partner_status == "In Transit" else "secondary"):
            update_partner_assignment_status(selected_tx_id, "Delivered")
            update_transaction_status(selected_tx_id, "Delivered")
            st.rerun()

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    
    # Toggle Route Map
    map_btn_label = t("btn_hide_route") if st.session_state.logistics_show_route_map else t("btn_view_route")
    if st.button(f"🗺️ {map_btn_label}", key=f"btn_map_toggle_{selected_tx_id}", use_container_width=True):
        st.session_state.logistics_show_route_map = not st.session_state.logistics_show_route_map
        st.rerun()

    if st.session_state.get("logistics_show_route_map", False):
        display_optimized_route_map(
            route=[f_loc, b_loc],
            farmer_names={f_loc: f_name},
            buyer_name=b_name,
            crop=p_crop,
            total_distance_km=calculated_distance_km,
            total_load_kg=t_qty,
            logistics_cost=float(active_assigned_partner.get("estimated_freight", 3500.0)) if active_assigned_partner else 3500.0,
        )

st.divider()

# =========================================================
# SECTION 5 — MULTI-STOP ROUTE OPTIMIZER (OR-TOOLS)
# =========================================================

with st.expander(f"🛣️ {t('route_optimizer_title')} — OR-Tools Multi-Stop Solver", expanded=False):
    st.caption(t("route_optimizer_caption"))

    available_locations = sorted(produce_df["location"].dropna().unique().tolist())
    destinations = ["Pune", "Mumbai", "Ahmednagar", "Nashik"]

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        selected_locations = st.multiselect(
            t("farm_collection_pts"),
            available_locations,
            default=[available_locations[0], available_locations[1]] if len(available_locations) >= 2 else available_locations,
            key="multi_stop_loc_select",
        )
    with col_r2:
        destination = st.selectbox(
            t("dest_mandi_hub"),
            destinations,
            index=0,
            key="multi_stop_dest_select",
        )

    if st.button(f"✦ {t('btn_solve_route')} →", type="primary", use_container_width=True, key="btn_solve_multi_stop"):
        if not selected_locations:
            st.warning(t("warn_select_collection_pt"))
        else:
            route_locations = list(selected_locations) + [destination]
            route_locations = list(dict.fromkeys(route_locations))

            with st.spinner(t("computing_route_optimization")):
                try:
                    result = optimize_route(
                        locations=route_locations,
                        start_location=selected_locations[0],
                        end_location=destination,
                        vehicle_capacity_kg=2500.0,
                        demands_kg=[200] * len(route_locations),
                    )
                    st.session_state["multi_route_points"] = route_locations
                    st.success(f"✅ {t('route_optimized_success')}")
                except Exception as e:
                    st.session_state["multi_route_points"] = route_locations
                    st.info(f"Using baseline collection coordinates: {e}")

    multi_pts = st.session_state.get("multi_route_points", selected_locations + [destination] if selected_locations else ["Nashik", destination])
    if multi_pts:
        st.markdown(f"**📍 {t('route_sequence')}:** {' ➔ '.join(multi_pts)}")
        coord_start = get_coordinates(multi_pts[0])
        m_map = folium.Map(location=[coord_start[0], coord_start[1]], zoom_start=8, tiles="OpenStreetMap")
        
        r_coords = []
        for idx, loc in enumerate(multi_pts):
            coords = get_coordinates(loc)
            r_coords.append(coords)
            is_dest = (idx == len(multi_pts) - 1)
            folium.Marker(
                location=[coords[0], coords[1]],
                popup=f"{'🛒 Destination' if is_dest else '🌾 Stop'}: {loc}",
                icon=folium.Icon(color="red" if is_dest else "green", icon="flag" if is_dest else "shopping-cart"),
            ).add_to(m_map)

        if len(r_coords) >= 2:
            folium.PolyLine(locations=r_coords, color="#183A2A", weight=4, opacity=0.85, dash_array="5, 10").add_to(m_map)

        st_folium(m_map, height=340, use_container_width=True, key="folium_multi_stop_map")

st.divider()
st.caption(f"ℹ️ {t('logistics_footer_caption')}")
