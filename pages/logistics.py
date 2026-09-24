"""
Logistics & Setu Load Fulfillment Dashboard | Kisan Setu
Theme: 'Bharat, Reimagined'
Operational Logistics Hub answering:
1. What deliveries are active?
2. Where do they need to go?
3. What is the route?
4. What vehicle/load is involved?
5. What is the current delivery status?
Reuses: maps.route_map, logistics.route_optimizer, utils.transactions, utils.data_loader, utils.translations
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
from utils.consumer_orders import (
    load_consumer_orders,
    update_consumer_order_status,
)
from utils.transactions import (
    update_transaction_status,
)
from logistics.route_optimizer import optimize_route
from maps.route_map import display_optimized_route_map, get_coordinates
from ai.matching import get_distance
from utils.translations import t, get_current_language

from ui.theme import inject_custom_theme
from ui.setu_components import (
    render_brand_header,
    render_bharat_market_pulse,
    render_setu_load,
    render_setu_score,
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

st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

# =========================================================
# 3. FLEET PROVIDER SELECTION & REAL DATA KPIS
# =========================================================

provider_options = logistics_df["provider_id"].astype(str).tolist() if not logistics_df.empty else ["L001"]
current_prov_id = st.session_state.get("user_id", "L001")
if not str(current_prov_id).startswith("L") or current_prov_id not in provider_options:
    current_prov_id = provider_options[0]

col_p_sel, col_p_meta = st.columns([1.8, 2.2])

with col_p_sel:
    selected_provider_id = st.selectbox(
        f"🚚 {t('select_transport_fleet')}",
        provider_options,
        index=provider_options.index(current_prov_id),
        format_func=lambda x: f"{x} · {logistics_df[logistics_df['provider_id']==x].iloc[0]['provider_name']} ({logistics_df[logistics_df['provider_id']==x].iloc[0]['vehicle_type']})" if not logistics_df.empty and x in logistics_df['provider_id'].values else str(x),
    )

provider = logistics_df[logistics_df["provider_id"] == selected_provider_id].iloc[0] if not logistics_df.empty and selected_provider_id in logistics_df['provider_id'].values else logistics_df.iloc[0]

total_capacity = float(provider.get("capacity_kg", 1000))
cost_per_km = float(provider.get("cost_per_km", 28.0))
base_cost = float(provider.get("base_cost", 500.0))
fleet_location = str(provider.get("location", "Nashik"))

with col_p_meta:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    chip_html = f"""
    <div style="background: rgba(22, 62, 43, 0.06); border: 1px solid rgba(22, 62, 43, 0.16); border-radius: 10px; padding: 8px 14px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
        <span style="font-weight: 800; color: #163E2B; font-size: 0.95rem;">🚛 {provider['provider_name']} · <span style="font-weight:600; color:#526058;">{provider['vehicle_type']}</span></span>
        <span style="font-size: 0.82rem; color: #526058; font-weight: 600;">📍 {fleet_location} · Base: ₹{base_cost:,.0f}</span>
    </div>
    """
    render_html(chip_html)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# Calculate Real Metrics from transactions.csv and consumer_orders.csv
active_txs = transactions_df[transactions_df["status"].astype(str).isin(["Order Placed", "Confirmed", "In Transit"])].copy()
in_transit_txs = transactions_df[transactions_df["status"].astype(str) == "In Transit"].copy()
delivered_txs = transactions_df[transactions_df["status"].astype(str).isin(["Delivered", "Completed"])].copy()

k1, k2, k3, k4 = st.columns(4)
k1.metric(f"📦 {t('active_deliveries_label')}", len(active_txs))
k2.metric(f"🚚 {t('in_transit_label')}", len(in_transit_txs))
k3.metric(f"✅ {t('delivered_label')}", len(delivered_txs))
k4.metric(f"🚛 {t('fleet_vehicles_label')}", f"{total_capacity:,.0f} kg", provider["vehicle_type"])

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# =========================================================
# 4. DELIVERY DETAIL & ROUTE MAP (WHEN SELECTED)
# =========================================================

if st.session_state.get("logistics_selected_delivery_id"):
    sel_tx_id = st.session_state.logistics_selected_delivery_id
    sel_tx_rows = transactions_df[transactions_df["transaction_id"].astype(str) == str(sel_tx_id)]
    
    if not sel_tx_rows.empty:
        sel_tx = sel_tx_rows.iloc[0]
        sel_status = str(sel_tx["status"])
        sel_f_id = str(sel_tx["farmer_id"])
        sel_b_id = str(sel_tx["buyer_id"])
        sel_p_id = str(sel_tx["produce_id"])
        sel_qty = float(sel_tx.get("quantity_kg", 500))
        sel_rate = float(sel_tx.get("price_per_kg", 30))
        sel_total = float(sel_tx.get("total_value", sel_qty * sel_rate))
        
        # Lookups
        f_rec = farmers_df[farmers_df["farmer_id"].astype(str) == sel_f_id]
        f_name_val = f_rec.iloc[0]["name"] if not f_rec.empty else f"Farmer {sel_f_id}"
        f_loc_val = f_rec.iloc[0]["village"] if not f_rec.empty else "Niphad"
        f_dist_val = f_rec.iloc[0]["district"] if not f_rec.empty else "Nashik"

        b_rec = buyers_df[buyers_df["buyer_id"].astype(str) == sel_b_id]
        b_name_val = b_rec.iloc[0]["name"] if not b_rec.empty else f"Buyer {sel_b_id}"
        b_loc_val = b_rec.iloc[0]["location"] if not b_rec.empty else "Pune"
        b_dist_val = b_rec.iloc[0]["district"] if not b_rec.empty else "Pune"

        p_rec = produce_df[produce_df["produce_id"].astype(str) == sel_p_id]
        p_crop_val = str(p_rec.iloc[0]["crop"]) if not p_rec.empty else "Onion"
        p_grade_val = str(p_rec.iloc[0]["quality_grade"]) if not p_rec.empty else "A"

        dist_km = float(get_distance(f_dist_val, b_dist_val))
        freight_amt = base_cost + (dist_km * cost_per_km)
        est_hours = max(1.0, round(dist_km / 45.0, 1))
        load_pct = min(100, int((sel_qty / total_capacity) * 100))

        status_color = "#E8B83D" if sel_status == "Order Placed" else (
            "#163E2B" if sel_status == "Confirmed" else (
                "#1952B3" if sel_status == "In Transit" else "#176536"
            )
        )
        status_key = f"status_{sel_status.lower().replace(' ', '_')}"
        status_text = t(status_key)

        with st.container(border=True):
            st.subheader(f"🚚 {t('delivery_detail_title')} — #{sel_tx_id}")
            
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                st.markdown(f"**🌾 {t('produce_label')}:** {crop_icons.get(p_crop_val.lower(), '🌱')} {p_crop_val} · Grade {p_grade_val} — #{sel_p_id}")
                st.markdown(f"**⚖️ {t('quantity_label')}:** {sel_qty:,.0f} kg")
                st.markdown(f"**📍 {t('origin_label')}:** {f_name_val} ({f_loc_val}, {f_dist_val})")
                st.markdown(f"**🏢 {t('destination_label')}:** {b_name_val} ({b_loc_val}, {b_dist_val})")
            with d_col2:
                st.markdown(f"**🚚 {t('estimated_distance_label')}:** {dist_km:.0f} km")
                st.markdown(f"**💰 {t('estimated_freight_label')}:** ₹{freight_amt:,.0f} (₹{cost_per_km:.0f}/km)")
                st.markdown(f"**⏱️ {t('estimated_travel_time')}:** ~{est_hours} hrs")
                st.markdown(f"**🚛 {t('vehicle_load_assigned')}:** {provider['vehicle_type']} ({load_pct}% load)")

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            
            # Action Buttons
            btn_act1, btn_act2, btn_act3 = st.columns([1.5, 1.5, 1])
            with btn_act1:
                btn_map_text = t("btn_hide_route") if st.session_state.logistics_show_route_map else t("btn_view_route")
                if st.button(f"🗺️ {btn_map_text}", use_container_width=True, key=f"btn_toggle_map_{sel_tx_id}"):
                    st.session_state.logistics_show_route_map = not st.session_state.logistics_show_route_map
                    st.rerun()
            with btn_act2:
                if sel_status == "Confirmed":
                    if st.button(f"🚚 {t('btn_dispatch_start')}", type="primary", use_container_width=True, key=f"btn_disp_{sel_tx_id}"):
                        update_transaction_status(sel_tx_id, "In Transit")
                        st.rerun()
                elif sel_status == "In Transit":
                    if st.button(f"📍 {t('btn_mark_delivered_logistics')}", type="primary", use_container_width=True, key=f"btn_deliv_{sel_tx_id}"):
                        update_transaction_status(sel_tx_id, "Delivered")
                        st.rerun()
                elif sel_status == "Delivered":
                    if st.button(f"🎉 {t('btn_complete_settle')}", type="primary", use_container_width=True, key=f"btn_comp_{sel_tx_id}"):
                        update_transaction_status(sel_tx_id, "Completed")
                        st.rerun()
                else:
                    st.markdown(f"<span style='color:{status_color}; font-weight:800;'>● {status_text}</span>", unsafe_allow_html=True)
            with btn_act3:
                if st.button(f"✕ {t('close')}", use_container_width=True, key=f"btn_close_detail_{sel_tx_id}"):
                    st.session_state.logistics_selected_delivery_id = None
                    st.session_state.logistics_show_route_map = False
                    st.rerun()

            # Render Route Map
            if st.session_state.get("logistics_show_route_map", False):
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                display_optimized_route_map(
                    route=[f_loc_val, b_loc_val],
                    farmer_names={f_loc_val: f_name_val},
                    buyer_name=b_name_val,
                    crop=p_crop_val,
                    total_distance_km=dist_km,
                    total_load_kg=sel_qty,
                    logistics_cost=freight_amt,
                )

        st.divider()

# =========================================================
# 5. ACTIVE DELIVERY BOARD
# =========================================================

st.subheader(f"🚚 {t('active_delivery_board_title')}")

if transactions_df.empty:
    render_empty_state(t("no_active_deliveries_title"), t("no_active_deliveries_desc"))
else:
    for _, tx_row in transactions_df.sort_values("date", ascending=False).iterrows():
        tx_id = str(tx_row["transaction_id"])
        status = str(tx_row["status"])
        f_id = str(tx_row["farmer_id"])
        b_id = str(tx_row["buyer_id"])
        p_id = str(tx_row.get("produce_id", ""))
        qty = float(tx_row.get("quantity_kg", 0))
        rate = float(tx_row.get("price_per_kg", 0))
        total_val = float(tx_row.get("total_value", qty * rate))
        tx_date = str(tx_row.get("date", ""))

        # Lookups
        f_match = farmers_df[farmers_df["farmer_id"].astype(str) == f_id]
        f_name = f_match.iloc[0]["name"] if not f_match.empty else f"Farmer {f_id}"
        f_origin = f"{f_match.iloc[0]['village']}, {f_match.iloc[0]['district']}" if not f_match.empty else "Niphad, Nashik"

        b_match = buyers_df[buyers_df["buyer_id"].astype(str) == b_id]
        b_name = b_match.iloc[0]["name"] if not b_match.empty else f"Buyer {b_id}"
        b_dest = b_match.iloc[0]["location"] if not b_match.empty else "Pune"

        p_match = produce_df[produce_df["produce_id"].astype(str) == p_id]
        p_crop = str(p_match.iloc[0]["crop"]) if not p_match.empty else "Onion"
        p_grade = str(p_match.iloc[0]["quality_grade"]) if not p_match.empty else "A"

        status_color = "#E8B83D" if status == "Order Placed" else (
            "#163E2B" if status == "Confirmed" else (
                "#1952B3" if status == "In Transit" else (
                    "#176536" if status in ["Delivered", "Completed"] else "#9E4932"
                )
            )
        )
        status_key = f"status_{status.lower().replace(' ', '_')}"
        status_text = t(status_key)

        is_currently_selected = (st.session_state.get("logistics_selected_delivery_id") == tx_id)

        with st.container(border=True):
            col_b1, col_b2, col_b3 = st.columns([2.5, 2.2, 1.3])
            with col_b1:
                st.markdown(f"### 🚚 {t('deal_number', deal_id=tx_id)}")
                st.write(f"**{t('produce_label')}:** {crop_icons.get(p_crop.lower(), '🌱')} {p_crop} (Grade {p_grade}) · **{qty:,.0f} kg**")
                st.caption(f"📍 **{t('origin_label')}:** {f_name} ({f_origin})")
                st.caption(f"🏢 **{t('destination_label')}:** {b_name} ({b_dest})")
            with col_b2:
                st.write(f"**{t('total_deal_val')}:** **₹{total_val:,.0f}** (@ ₹{rate:.2f}/kg)")
                st.markdown(f"{t('status')}: <span style='color:{status_color}; font-weight:800;'>● {status_text}</span>", unsafe_allow_html=True)
                st.caption(f"📅 {t('date')}: {tx_date}")
            with col_b3:
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                btn_lbl = t("btn_hide_delivery") if is_currently_selected else t("btn_view_delivery")
                if st.button(f"👁 {btn_lbl}", key=f"btn_sel_deliv_{tx_id}", use_container_width=True, type="primary" if is_currently_selected else "secondary"):
                    st.session_state.logistics_selected_delivery_id = None if is_currently_selected else tx_id
                    st.session_state.logistics_show_route_map = False
                    st.rerun()

st.divider()

# =========================================================
# 6. MULTI-STOP ROUTE OPTIMIZER (OR-TOOLS)
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
                        vehicle_capacity_kg=total_capacity,
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
