"""
Complete Transactions Lifecycle Manager | Kisan Setu
Theme: 'Bharat, Reimagined'
Tracks transactions across all ecosystem nodes from initiation to fulfillment.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from utils.data_loader import (
    load_transactions,
    load_farmers,
    load_buyers,
    load_produce,
)
from utils.transactions import update_transaction_status
from utils.translations import t, get_current_language
from ui.theme import inject_custom_theme
from ui.setu_components import (
    render_brand_header,
    render_bharat_market_pulse,
    render_empty_state,
)

inject_custom_theme()

language = get_current_language()

transactions = load_transactions()
farmers = load_farmers()
buyers = load_buyers()
produce = load_produce()

render_bharat_market_pulse()

# Brand Header with Logo
render_brand_header(
    title=f"{t('brand_transactions_title')}",
    subtitle=t("brand_transactions_sub"),
    badge=t("badge_trade_ledger"),
)

st.divider()

if transactions.empty:
    render_empty_state(t("no_transactions_recorded"), t("deals_initiated_appear"))
    st.stop()

# Prepare Data
transactions["quantity_kg"] = pd.to_numeric(transactions["quantity_kg"], errors="coerce").fillna(0)
transactions["price_per_kg"] = pd.to_numeric(transactions["price_per_kg"], errors="coerce").fillna(0)
transactions["total_value"] = pd.to_numeric(transactions["total_value"], errors="coerce").fillna(
    transactions["quantity_kg"] * transactions["price_per_kg"]
)

total_tx = len(transactions)
total_gross = transactions["total_value"].sum()
in_progress = len(transactions[transactions["status"].isin(["Order Placed", "Confirmed", "In Transit"])])
completed = len(transactions[transactions["status"] == "Completed"])

m1, m2, m3, m4 = st.columns(4)
m1.metric(f"💳 {t('total_transactions')}", total_tx)
m2.metric(f"💰 {t('gross_trade_val')}", f"₹{total_gross:,.0f}")
m3.metric(f"🚚 {t('in_active_fulfilment')}", in_progress)
m4.metric(f"✅ {t('completed_settled')}", completed)

st.divider()

# Filter by Status
st.subheader(f"📋 {t('transactions_pipeline_title')}")

status_filter = st.selectbox(
    t("filter_by_status"),
    ["All", "Order Placed", "Confirmed", "In Transit", "Delivered", "Completed", "Rejected"],
)

filtered = transactions.copy()
if status_filter != "All":
    filtered = filtered[filtered["status"] == status_filter]

if filtered.empty:
    render_empty_state(t("no_tx_with_status", status=status_filter), t("select_all_to_view"))
else:
    for _, tx in filtered.iterrows():
        tx_id = tx["transaction_id"]
        status = tx["status"]
        status_color = "#176536" if status in ["Completed", "Confirmed"] else ("#1952B3" if status == "In Transit" else ("#E8B83D" if status == "Order Placed" else "#9E4932"))
        status_key = f"status_{status.lower().replace(' ', '_')}"
        status_text = t(status_key)

        with st.container(border=True):
            c1, c2, c3 = st.columns([2.5, 2, 1.5])
            with c1:
                st.markdown(f"### 🤝 {t('transaction_num', tx_id=tx_id)}")
                st.write(f"Farmer ID: **{tx['farmer_id']}** ➔ Buyer ID: **{tx['buyer_id']}**")
                st.write(f"{t('produce_lot')}: **{tx['produce_id']}** · {t('volume')}: **{float(tx['quantity_kg']):,.0f} kg**")
            with c2:
                st.write(f"{t('unit_rate')}: **₹{float(tx['price_per_kg']):.2f}/kg**")
                st.write(f"{t('total_deal_val')}: **₹{float(tx['total_value']):,.0f}**")
                st.markdown(f"{t('status')}: <span style='color:{status_color}; font-weight:800;'>● {status_text}</span>", unsafe_allow_html=True)
                st.caption(f"📅 {t('trade_date')}: {tx['date']}")
            with c3:
                st.caption(t("admin_status_override"))
                status_choices = ["Order Placed", "Confirmed", "In Transit", "Delivered", "Completed", "Rejected"]
                new_status = st.selectbox(
                    t("update_status_label"),
                    status_choices,
                    index=status_choices.index(status) if status in status_choices else 0,
                    key=f"status_sel_{tx_id}",
                )
                if new_status != status:
                    if st.button(t("btn_save"), key=f"btn_save_{tx_id}"):
                        update_transaction_status(tx_id, new_status)
                        st.success(t("status_updated_msg"))
                        st.rerun()

st.caption(f"ℹ️ {t('transactions_footer')}")