"""
Farmer Orders Management | Kisan Setu
Theme: 'Bharat, Reimagined'
Tracks complete order lifecycle across B2B Wholesale Deals and B2C Consumer Orders.
"""

import streamlit as st
import pandas as pd

from utils.data_loader import load_farmers, load_buyers, load_produce
from utils.consumer_orders import (
    load_consumer_orders,
    update_consumer_order_status,
)
from utils.transactions import (
    load_transactions,
    get_farmer_transactions,
    update_transaction_status,
)
from utils.translations import t, get_current_language
from ui.theme import inject_custom_theme
from ui.setu_components import (
    render_brand_header,
    render_bharat_market_pulse,
    render_empty_state,
)

inject_custom_theme()

language = get_current_language()

# Header & Pulse
render_bharat_market_pulse()

# Brand Header with Logo
render_brand_header(
    title=f"{t('brand_farmer_orders_title')}",
    subtitle=t("brand_farmer_orders_sub"),
    badge=t("badge_orders_active"),
)

st.divider()

# Load Data
farmers = load_farmers()
buyers = load_buyers()
produce_df = load_produce()
consumer_orders = load_consumer_orders()
all_transactions = load_transactions()

crop_icons = {
    "onion": "🧅",
    "tomato": "🍅",
    "potato": "🥔",
    "wheat": "🌾",
    "banana": "🍌",
    "ginger": "🫚",
    "rice": "🍚",
}

produce_map = {}
if not produce_df.empty:
    for _, p_row in produce_df.iterrows():
        p_id = str(p_row.get("produce_id", "")).strip()
        crop_name = str(p_row.get("crop", "Produce"))
        grade = str(p_row.get("quality_grade", "A"))
        c_icon = crop_icons.get(crop_name.lower(), "🌱")
        produce_map[p_id] = f"{c_icon} {crop_name} (Grade {grade}) — #{p_id}"

current_user_id = st.session_state.get("user_id", "F001")
farmer_options = farmers["farmer_id"].tolist()

default_idx = farmer_options.index(current_user_id) if current_user_id in farmer_options else 0

col_top1, col_top2 = st.columns([2, 1])

with col_top1:
    selected_farmer_id = st.selectbox(
        t("active_farmer_profile"),
        farmer_options,
        index=default_idx,
        format_func=lambda x: f"{x} · {farmers[farmers['farmer_id']==x].iloc[0]['name']} ({farmers[farmers['farmer_id']==x].iloc[0]['village']}, {farmers[farmers['farmer_id']==x].iloc[0]['district']})",
    )

farmer_row = farmers[farmers["farmer_id"] == selected_farmer_id].iloc[0]

# Filter orders for selected farmer
b2b_transactions = get_farmer_transactions(selected_farmer_id)
b2c_orders = consumer_orders[consumer_orders["farmer_id"].astype(str) == str(selected_farmer_id)].copy()

# Summary Metrics (Combined B2B + B2C)
total_b2b = len(b2b_transactions)
total_b2c = len(b2c_orders)
total_active = len(b2b_transactions[b2b_transactions["status"].isin(["Order Placed", "Confirmed", "In Transit", "Delivered"])]) + len(b2c_orders[b2c_orders["status"].isin(["Order Placed", "Confirmed", "In Transit", "Delivered"])])
total_settled = len(b2b_transactions[b2b_transactions["status"] == "Completed"]) + len(b2c_orders[b2c_orders["status"] == "Completed"])

m1, m2, m3, m4 = st.columns(4)
m1.metric(f"🏢 {t('tab_b2b_deals')}", total_b2b)
m2.metric(f"🛍️ {t('tab_b2c_orders')}", total_b2c)
m3.metric(f"🚚 {t('in_fulfilment')}", total_active)
m4.metric(f"✅ {t('completed_settled')}", total_settled)

st.divider()

# Two-Tab Structure: B2B Wholesale Deals vs B2C Consumer Orders
tab_b2b, tab_b2c = st.tabs([
    f"🏢 {t('tab_b2b_deals')}",
    f"🛍️ {t('tab_b2c_orders')}",
])

# ============================================================
# TAB 1: B2B WHOLESALE DEALS (transactions.csv)
# ============================================================
with tab_b2b:
    st.subheader(f"🏢 {t('b2b_subhead')}")
    st.caption(t("b2b_subhead_caption"))

    if b2b_transactions.empty:
        render_empty_state(
            t("no_b2b_deals_title"),
            t("no_b2b_deals_desc"),
            t("no_b2b_deals_action"),
        )
    else:
        # Buyer name lookup map
        buyer_name_map = {}
        if not buyers.empty:
            for _, b_row in buyers.iterrows():
                buyer_name_map[str(b_row["buyer_id"])] = f"{b_row['name']} ({b_row.get('location', b_row.get('district', ''))})"

        for _, tx in b2b_transactions.iterrows():
            tx_id = tx["transaction_id"]
            status = tx["status"]
            b_id = str(tx["buyer_id"])
            buyer_label = buyer_name_map.get(b_id, f"Buyer {b_id}")
            qty = float(tx["quantity_kg"])
            rate = float(tx["price_per_kg"])
            total_val = float(tx["total_value"])
            tx_date = tx.get("date", "")
            produce_id = tx.get("produce_id", "")

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
                c1, c2, c3 = st.columns([2.5, 2, 1.5])
                with c1:
                    st.markdown(f"### 🤝 {t('deal_number', deal_id=tx_id)}")
                    st.write(f"**{t('buyer')}:** {buyer_label}")
                    produce_info = produce_map.get(str(produce_id).strip(), f"#{produce_id}")
                    st.write(f"**{t('produce_lot')}:** {produce_info}")
                    st.write(f"**{t('volume')}:** {qty:,.0f} kg")
                with c2:
                    st.write(f"**{t('unit_rate')}:** ₹{rate:.2f}/kg")
                    st.write(f"**{t('total_realization')}:** **₹{total_val:,.2f}**")
                    st.markdown(f"{t('status')}: <span style='color:{status_color}; font-weight:800;'>● {status_text}</span>", unsafe_allow_html=True)
                    st.caption(f"📅 {t('date')}: {tx_date}")
                with c3:
                    if status == "Order Placed":
                        if st.button(f"✅ {t('btn_confirm_deal')}", key=f"f_b2b_conf_{tx_id}", type="primary", use_container_width=True):
                            update_transaction_status(tx_id, "Confirmed")
                            st.success(f"Deal {tx_id} confirmed!")
                            st.rerun()
                        if st.button(f"❌ {t('btn_reject')}", key=f"f_b2b_rej_{tx_id}", use_container_width=True):
                            update_transaction_status(tx_id, "Rejected")
                            st.warning(f"Deal {tx_id} rejected.")
                            st.rerun()
                    elif status == "Confirmed":
                        if st.button(f"🚚 {t('btn_mark_in_transit')}", key=f"f_b2b_disp_{tx_id}", type="primary", use_container_width=True):
                            update_transaction_status(tx_id, "In Transit")
                            st.rerun()
                    elif status == "In Transit":
                        if st.button(f"📍 {t('btn_mark_delivered')}", key=f"f_b2b_del_{tx_id}", use_container_width=True):
                            update_transaction_status(tx_id, "Delivered")
                            st.rerun()
                    elif status == "Delivered":
                        if st.button(f"🎉 {t('btn_complete_deal')}", key=f"f_b2b_comp_{tx_id}", type="primary", use_container_width=True):
                            update_transaction_status(tx_id, "Completed")
                            st.rerun()
                    elif status == "Completed":
                        st.markdown(f"<span style='color:#176536; font-weight:700;'>✓ {t('payment_settled')}</span>", unsafe_allow_html=True)

# ============================================================
# TAB 2: B2C CONSUMER ORDERS (consumer_orders.csv)
# ============================================================
with tab_b2c:
    st.subheader(f"🛍️ {t('b2c_subhead')}")
    st.caption(t("b2c_subhead_caption"))

    if b2c_orders.empty:
        render_empty_state(
            t("no_consumer_orders_title"),
            t("no_consumer_orders_desc"),
            t("no_consumer_orders_action"),
        )
    else:
        pending_c = b2c_orders[b2c_orders["status"] == "Order Placed"]
        active_c = b2c_orders[b2c_orders["status"].isin(["Confirmed", "In Transit", "Delivered", "Completed", "Rejected"])]

        if not pending_c.empty:
            st.markdown(f"#### 🔔 {t('incoming_orders_req_conf')}")
            for _, order in pending_c.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2.5, 2, 1.5])
                    with c1:
                        st.markdown(f"### 🛒 {t('order_number', order_id=order['order_id'])}")
                        st.write(f"**{t('customer')}:** {order['consumer_name']}")
                        st.write(f"**{t('commodity')}:** {order['crop']} · {float(order['quantity_kg']):.0f} kg")
                    with c2:
                        st.write(f"**{t('price_rate')}:** ₹{float(order['price_per_kg']):.2f}/kg")
                        st.write(f"**{t('total_realization')}:** **₹{float(order['total_value']):,.2f}**")
                        st.caption(f"📅 {t('ordered_date')}: {order['date']}")
                    with c3:
                        if st.button(f"✅ {t('btn_confirm_order')}", key=f"conf_{order['order_id']}", type="primary", use_container_width=True):
                            update_consumer_order_status(order["order_id"], "Confirmed")
                            st.success(f"Order {order['order_id']} confirmed!")
                            st.rerun()
                        if st.button(f"❌ {t('btn_reject')}", key=f"rej_{order['order_id']}", use_container_width=True):
                            update_consumer_order_status(order["order_id"], "Rejected")
                            st.warning(f"Order {order['order_id']} rejected.")
                            st.rerun()

        if not active_c.empty:
            st.markdown(f"#### 🚚 {t('orders_fulfilment_history')}")
            for _, order in active_c.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2.5, 2, 1.5])
                    with c1:
                        st.markdown(f"### 📦 {t('order_number', order_id=order['order_id'])}")
                        st.write(f"**{t('customer')}:** {order['consumer_name']}")
                        st.write(f"**{t('batch')}:** {order['crop']} ({float(order['quantity_kg']):.0f} kg)")
                    with c2:
                        st.write(f"**{t('order_total')}:** **₹{float(order['total_value']):,.2f}**")
                        c_status = order["status"]
                        status_color = "#176536" if c_status in ["Confirmed", "Completed"] else ("#1952B3" if c_status == "In Transit" else "#5B2B82")
                        status_key = f"status_{c_status.lower().replace(' ', '_')}"
                        status_text = t(status_key)
                        st.markdown(f"{t('status')}: <span style='color:{status_color}; font-weight:800;'>● {status_text}</span>", unsafe_allow_html=True)
                        st.caption(f"📅 {t('date')}: {order['date']}")
                    with c3:
                        if order["status"] == "Confirmed":
                            if st.button(f"🚚 {t('btn_mark_in_transit')}", key=f"disp_{order['order_id']}", type="primary", use_container_width=True):
                                update_consumer_order_status(order["order_id"], "In Transit")
                                st.rerun()
                        elif order["status"] == "In Transit":
                            if st.button(f"📍 {t('btn_mark_delivered')}", key=f"del_{order['order_id']}", use_container_width=True):
                                update_consumer_order_status(order["order_id"], "Delivered")
                                st.rerun()
                        elif order["status"] == "Delivered":
                            if st.button(f"🎉 {t('btn_complete')}", key=f"comp_{order['order_id']}", type="primary", use_container_width=True):
                                update_consumer_order_status(order["order_id"], "Completed")
                                st.rerun()

st.divider()
st.caption(f"ℹ️ {t('farmer_orders_footer')}")