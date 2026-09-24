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
    load_payments,
)
from utils.transactions import update_transaction_status
from utils.payment_settlement import (
    get_payment_for_transaction,
    record_or_update_payment,
    update_payment_status,
    update_settlement_status,
    calculate_settlement_breakdown,
    DISCLAIMER_TEXT,
)
from logistics.partner_manager import get_partner_for_transaction
from utils.translations import t, get_current_language
from ui.theme import inject_custom_theme
from ui.setu_components import (
    render_brand_header,
    render_bharat_market_pulse,
    render_empty_state,
    render_html,
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

            # LOGISTICS PARTNER SECTION
            assigned_partner = get_partner_for_transaction(tx_id)
            if assigned_partner:
                p_name = assigned_partner.get("partner_name", "Partner Fleet")
                p_veh = assigned_partner.get("vehicle", "Mini Truck")
                p_freight = float(assigned_partner.get("estimated_freight", 0.0))
                p_stat = assigned_partner.get("status", "Assigned")
                st.markdown(
                    f"""
                    <div style="background: rgba(22, 62, 43, 0.04); border: 1px solid rgba(22, 62, 43, 0.15); border-radius: 8px; padding: 10px 14px; margin-top: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px;">
                            <span style="font-weight: 800; color: #163E2B; font-size: 0.86rem;">🚚 Logistics Partner: {p_name}</span>
                            <span style="font-size: 0.76rem; background: #163E2B; color: #FFFFFF; padding: 2px 8px; border-radius: 4px; font-weight: 700;">Status: {p_stat}</span>
                        </div>
                        <div style="font-size: 0.82rem; color: #526058; margin-top: 4px;">
                            <b>Vehicle:</b> {p_veh} · <b>Freight:</b> ₹{p_freight:,.0f} · <b>Route:</b> {assigned_partner.get('pickup_location')} ➔ {assigned_partner.get('destination')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                    <div style="background: #FFFBF5; border: 1px dashed #E5DFD3; border-radius: 8px; padding: 8px 14px; margin-top: 8px; font-size: 0.82rem; color: #8A7A64;">
                        🚚 <i>Logistics partner not assigned</i> — <a href="/logistics" style="color: #163E2B; font-weight: 700;">Assign via Logistics Hub</a>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # PAYMENT & SETTLEMENT SECTION
            st.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px dashed #E5DFD3;' />", unsafe_allow_html=True)
            
            pay_rec = get_payment_for_transaction(tx_id)
            if not pay_rec:
                logistics_cost_val = float(assigned_partner.get("estimated_freight", 0.0)) if assigned_partner else 0.0
                pay_rec = record_or_update_payment(
                    transaction_id=tx_id,
                    buyer_id=str(tx["buyer_id"]),
                    farmer_id=str(tx["farmer_id"]),
                    gross_amount=float(tx["total_value"]),
                    logistics_cost=logistics_cost_val,
                    platform_fee=0.0,
                    payment_status="Payment Received" if status in ["Delivered", "Completed"] else "Payment Pending",
                    settlement_status="Settled" if status == "Completed" else "Settlement Pending",
                )

            gross_val = float(pay_rec.get("gross_amount", tx["total_value"]))
            logistics_val = float(pay_rec.get("logistics_cost", 0.0))
            fee_val = float(pay_rec.get("platform_fee", 0.0))
            settlement_val = float(pay_rec.get("net_settlement", gross_val - logistics_val - fee_val))
            p_status = str(pay_rec.get("payment_status", "Payment Pending"))
            s_status = str(pay_rec.get("settlement_status", "Settlement Pending"))

            p_status_badge = "🟢 Received" if p_status == "Payment Received" else ("🔴 " + p_status if p_status in ["Failed", "Refunded"] else "🟡 Pending")
            s_status_badge = "🟢 Settled" if s_status == "Settled" else ("🔴 " + s_status if s_status == "Cancelled" else "🟡 Pending")

            st.markdown(
                f"""
                <div style="background: #FBF9F4; border: 1px solid #EBE4D8; border-radius: 10px; padding: 12px 16px; margin-top: 6px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-weight: 800; font-size: 0.85rem; color: #163E2B; letter-spacing: 0.04em;">💳 PAYMENT & SETTLEMENT</span>
                        <span style="font-size: 0.76rem; color: #68756C; font-style: italic;">{DISCLAIMER_TEXT}</span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 10px; font-size: 0.84rem;">
                        <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-radius: 6px; padding: 6px 10px;">
                            <div style="color: #68756C; font-size: 0.72rem; text-transform: uppercase;">Transaction Value</div>
                            <div style="font-weight: 800; color: #183A2A; font-size: 1.05rem;">₹{gross_val:,.0f}</div>
                        </div>
                        <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-radius: 6px; padding: 6px 10px;">
                            <div style="color: #68756C; font-size: 0.72rem; text-transform: uppercase;">Logistics</div>
                            <div style="font-weight: 800; color: #B85C38; font-size: 1.05rem;">- ₹{logistics_val:,.0f}</div>
                        </div>
                        <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-radius: 6px; padding: 6px 10px;">
                            <div style="color: #68756C; font-size: 0.72rem; text-transform: uppercase;">Platform Fee</div>
                            <div style="font-weight: 800; color: #68756C; font-size: 1.05rem;">- ₹{fee_val:,.0f}</div>
                        </div>
                        <div style="background: #EAF5ED; border: 1px solid #C4E3CB; border-radius: 6px; padding: 6px 10px;">
                            <div style="color: #176536; font-size: 0.72rem; text-transform: uppercase; font-weight: 700;">Farmer Settlement</div>
                            <div style="font-weight: 900; color: #176536; font-size: 1.1rem;">₹{settlement_val:,.0f}</div>
                        </div>
                        <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-radius: 6px; padding: 6px 10px;">
                            <div style="color: #68756C; font-size: 0.72rem; text-transform: uppercase;">Payment Status</div>
                            <div style="font-weight: 800; font-size: 0.88rem; margin-top: 2px;">{p_status_badge}</div>
                        </div>
                        <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-radius: 6px; padding: 6px 10px;">
                            <div style="color: #68756C; font-size: 0.72rem; text-transform: uppercase;">Settlement Status</div>
                            <div style="font-weight: 800; font-size: 0.88rem; margin-top: 2px;">{s_status_badge}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Interactive action triggers for payment lifecycle simulation
            pay_col1, pay_col2 = st.columns([1, 1])
            with pay_col1:
                if p_status == "Payment Pending":
                    if st.button("💵 Receive Payment (Simulate)", key=f"btn_pay_recv_{tx_id}", use_container_width=True):
                        update_payment_status(tx_id, "Payment Received")
                        st.success("Payment Received recorded.")
                        st.rerun()
            with pay_col2:
                if p_status == "Payment Received" and s_status == "Settlement Pending":
                    if st.button("🏦 Settle to Farmer (Simulate)", key=f"btn_settle_{tx_id}", use_container_width=True, type="primary"):
                        update_settlement_status(tx_id, "Settled")
                        st.success("Farmer Settlement completed.")
                        st.rerun()

st.caption(f"ℹ️ {t('transactions_footer')}")