"""
Consumer Farm-to-Table Marketplace | Kisan Setu
Theme: 'Bharat, Reimagined'
Consumer-First Shopping Experience: Direct Farm Sourcing, Product Details, Order Confirmation, and Order Tracking.
Reuses: utils.consumer_orders, utils.data_loader, utils.translations
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date

from utils.data_loader import load_produce, load_farmers
from utils.consumer_orders import (
    load_consumer_orders,
    create_consumer_order,
)
from utils.translations import t, get_current_language
from ui.theme import inject_custom_theme
from ui.setu_components import (
    render_brand_header,
    render_bharat_market_pulse,
    render_empty_state,
    render_html,
)

# ============================================================
# 1. THEME & INITIALIZATION
# ============================================================

inject_custom_theme()
language = get_current_language()

# Load Core Data
produce_df = load_produce()
farmers_df = load_farmers()
orders_df = load_consumer_orders()

# Active Consumer Session
consumer_id = st.session_state.get("user_id", "C001")
if not str(consumer_id).startswith("C"):
    consumer_id = "C001"
consumer_name = st.session_state.get("user_name", "Pooja Sharma")

# State Management
if "consumer_active_view_lot_id" not in st.session_state:
    st.session_state.consumer_active_view_lot_id = None

if "consumer_confirming_order" not in st.session_state:
    st.session_state.consumer_confirming_order = None

if "consumer_last_order" not in st.session_state:
    st.session_state.consumer_last_order = None

# Crop Icon Map
crop_icons = {
    "onion": "🧅",
    "tomato": "🍅",
    "potato": "🥔",
    "wheat": "🌾",
    "banana": "🍌",
    "ginger": "🫚",
    "rice": "🍚",
}

def get_produce_photo_path(produce_id):
    uploads_dir = Path("assets/uploads") / str(produce_id).strip()
    if uploads_dir.exists():
        for ext in [".png", ".jpg", ".jpeg", ".webp"]:
            p = uploads_dir / f"photo_1{ext}"
            if p.exists():
                return str(p)
            files = list(uploads_dir.glob(f"*{ext}"))
            if files:
                return str(files[0])
    return None

# ============================================================
# 2. BRAND HEADER & TOP BANNER
# ============================================================

render_bharat_market_pulse()

render_brand_header(
    title=t("consumer_hub_title"),
    subtitle=t("consumer_hub_sub"),
    badge=t("badge_provenance"),
)

st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

# ============================================================
# 3. CONSUMER IDENTITY & REAL DATA KPIS
# ============================================================

available_produce = produce_df[produce_df["status"].astype(str).str.lower() == "available"].copy()
consumer_orders = orders_df[orders_df["consumer_id"].astype(str) == str(consumer_id)].copy()

active_orders_cnt = len(consumer_orders[consumer_orders["status"].astype(str).isin(["Order Placed", "Confirmed", "In Transit"])])
completed_orders_cnt = len(consumer_orders[consumer_orders["status"].astype(str).isin(["Delivered", "Completed"])])

col_c_prof, col_c_kpi = st.columns([1.5, 2.5])

with col_c_prof:
    st.markdown(
        f"""
        <div style="background: rgba(22, 62, 43, 0.06); border: 1px solid rgba(22, 62, 43, 0.16); border-radius: 12px; padding: 10px 16px;">
            <div style="font-size: 0.80rem; font-weight: 700; color: #526058; text-transform: uppercase;">🛍️ {t('your_consumer_profile')}</div>
            <div style="font-size: 1.1rem; font-weight: 800; color: #163E2B;">{consumer_name} <span style="font-size: 0.85rem; font-weight:600; color:#526058;">(#{consumer_id})</span></div>
            <div style="font-size: 0.82rem; color: #176536; font-weight: 600;">✓ Direct Farm-to-Table Verified</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_c_kpi:
    k1, k2, k3 = st.columns(3)
    k1.metric(f"🌾 {t('available_produce_title')}", len(available_produce))
    k2.metric(f"🚚 {t('active_orders_label')}", active_orders_cnt)
    k3.metric(f"✅ {t('completed_orders_label')}", completed_orders_cnt)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# ============================================================
# 4. ORDER CONFIRMATION MODAL & SUCCESS STATES
# ============================================================

if st.session_state.get("consumer_confirming_order"):
    conf_data = st.session_state.consumer_confirming_order
    with st.container(border=True):
        st.warning(f"🛒 **{t('confirm_consumer_order_title')}**")
        st.markdown(f"*{t('confirm_consumer_order_sub')}*")
        
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            st.markdown(f"**🌾 {t('produce_label')}:** {conf_data['crop']} (Grade {conf_data['grade']}) — #{conf_data['produce_id']}")
            st.markdown(f"**👨‍🌾 {t('farmer_label')}:** {conf_data['farmer_name']} ({conf_data['location']})")
            st.markdown(f"**⚖️ {t('quantity_label')}:** {conf_data['quantity_kg']:,.0f} kg")
        with c_col2:
            st.markdown(f"**💰 {t('price_label')}:** ₹{conf_data['price_per_kg']:.2f}/kg")
            st.markdown(f"**💵 {t('total_value_label')}:** ₹{conf_data['total_value']:,.2f}")
            st.markdown(f"**📍 {t('farm_source_label')}:** {conf_data['location']}, {conf_data['district']}")

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        btn_oc1, btn_oc2 = st.columns(2)
        with btn_oc1:
            if st.button(f"🛒 {t('btn_confirm_order_now')}", type="primary", use_container_width=True, key="btn_exec_consumer_order"):
                try:
                    new_order = create_consumer_order(
                        consumer_id=consumer_id,
                        consumer_name=consumer_name,
                        produce_id=conf_data["produce_id"],
                        farmer_id=conf_data["farmer_id"],
                        crop=conf_data["crop"],
                        quantity_kg=conf_data["quantity_kg"],
                        price_per_kg=conf_data["price_per_kg"],
                    )
                    st.session_state.consumer_confirming_order = None
                    st.session_state.consumer_last_order = new_order
                    st.rerun()
                except Exception as e:
                    st.error(f"Error creating order: {e}")
        with btn_oc2:
            if st.button(f"✕ {t('btn_cancel_deal')}", use_container_width=True, key="btn_cancel_consumer_order"):
                st.session_state.consumer_confirming_order = None
                st.rerun()
    st.divider()

if st.session_state.get("consumer_last_order"):
    last_ord = st.session_state.consumer_last_order
    with st.container(border=True):
        st.success(f"✓ **{t('consumer_order_success_title')} — #{last_ord['order_id']}**")
        st.markdown(t("consumer_order_success_desc"))
        
        suc1, suc2 = st.columns(2)
        with suc1:
            st.markdown(f"**📋 {t('order_id_label')}:** #{last_ord['order_id']}")
            st.markdown(f"**🌾 {t('produce_label')}:** {last_ord['crop']}")
            st.markdown(f"**👨‍🌾 {t('farmer_label')}:** Farmer {last_ord['farmer_id']}")
        with suc2:
            st.markdown(f"**⚖️ {t('quantity_label')}:** {float(last_ord['quantity_kg']):,.0f} kg")
            st.markdown(f"**💵 {t('total_value_label')}:** ₹{float(last_ord['total_value']):,.2f}")
            st.markdown(f"**📊 {t('status_label')}:** `{last_ord['status']}`")

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        btn_os1, btn_os2 = st.columns(2)
        with btn_os1:
            if st.button(f"📦 {t('btn_view_my_orders')} →", type="primary", use_container_width=True, key="btn_view_orders_after_succ"):
                st.session_state.consumer_last_order = None
                st.session_state.scroll_to_orders = True
                st.rerun()
        with btn_os2:
            if st.button(f"✕ {t('close')}", use_container_width=True, key="btn_close_succ_msg"):
                st.session_state.consumer_last_order = None
                st.rerun()
    st.divider()

# ============================================================
# 5. SEARCH & FILTER SECTION
# ============================================================

st.subheader(f"🌾 {t('todays_harvest_title')}")
st.caption(t("todays_harvest_caption"))

col_srch, col_grd, col_srt = st.columns([2.2, 1.2, 1.6])

with col_srch:
    search_query = st.text_input(
        f"🔍 {t('search_produce_placeholder')}",
        placeholder=t("search_produce_placeholder"),
        label_visibility="collapsed",
    )

with col_grd:
    grade_filter = st.selectbox(
        t("grade_input"),
        [t("all_grades_label"), "A", "B", "C"],
        label_visibility="collapsed",
    )

with col_srt:
    sort_option = st.selectbox(
        t("sort_by_label"),
        [
            t("sort_price_low_high"),
            t("sort_price_high_low"),
            t("sort_qty_high_low"),
        ],
        label_visibility="collapsed",
    )

# Filter Data
filtered_produce = available_produce.copy()

if search_query.strip():
    q = search_query.strip().lower()
    filtered_produce = filtered_produce[filtered_produce["crop"].astype(str).str.lower().str.contains(q)]

if grade_filter != t("all_grades_label"):
    filtered_produce = filtered_produce[filtered_produce["quality_grade"].astype(str).str.upper() == grade_filter]

if sort_option == t("sort_price_low_high"):
    filtered_produce = filtered_produce.sort_values("expected_price_per_kg", ascending=True)
elif sort_option == t("sort_price_high_low"):
    filtered_produce = filtered_produce.sort_values("expected_price_per_kg", ascending=False)
elif sort_option == t("sort_qty_high_low"):
    filtered_produce = filtered_produce.sort_values("quantity_kg", ascending=False)

st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

# ============================================================
# 6. PRODUCE BROWSE & PRODUCT DETAILS
# ============================================================

if filtered_produce.empty:
    render_empty_state(t("no_produce_matches_filter"), t("try_selecting_all"))
else:
    for idx, item in filtered_produce.iterrows():
        p_id = str(item["produce_id"])
        crop = str(item["crop"])
        qty = float(item["quantity_kg"])
        grade = str(item["quality_grade"])
        loc = str(item["location"])
        dist = str(item["district"])
        price = float(item["expected_price_per_kg"])
        h_date = str(item["available_date"])
        farmer_id = str(item["farmer_id"])
        
        # Farmer Name Lookup
        f_rec = farmers_df[farmers_df["farmer_id"].astype(str) == farmer_id]
        farmer_name_str = f_rec.iloc[0]["name"] if not f_rec.empty else f"Farmer {farmer_id}"
        
        photo_path = get_produce_photo_path(p_id)
        c_icon = crop_icons.get(crop.lower(), "🌱")

        with st.container(border=True):
            col_img, col_info, col_order = st.columns([1.2, 2.5, 1.8])

            with col_img:
                if photo_path and Path(photo_path).exists():
                    st.image(photo_path, use_container_width=True)
                else:
                    st.markdown(
                        f"""
                        <div style="background: rgba(22, 62, 43, 0.05); border: 1.5px dashed rgba(22, 62, 43, 0.2); border-radius: 12px; height: 110px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #526058;">
                            <span style="font-size: 2.2rem;">{c_icon}</span>
                            <span style="font-size: 0.72rem; font-weight: 600; margin-top: 4px;">{t('no_product_photo')}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            with col_info:
                st.markdown(f"### {c_icon} {crop} · {t('grade_label', grade=grade)}")
                st.markdown(
                    f"""
                    <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 6px;">
                        <span style="background: #E6F5EC; color: #176536; font-size: 0.75rem; font-weight: 700; padding: 2px 8px; border-radius: 4px;">✓ {farmer_name_str}</span>
                        <span style="background: #FAF7F0; border: 1px solid #E5DFD3; color: #526058; font-size: 0.75rem; padding: 2px 8px; border-radius: 4px;">📍 {loc}, {dist}</span>
                        <span style="background: #FAF7F0; border: 1px solid #E5DFD3; color: #526058; font-size: 0.75rem; padding: 2px 8px; border-radius: 4px;">📅 {h_date}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.write(f"{t('available_qty_label')}: **{qty:,.0f} kg** · Lot **#{p_id}**")
                st.markdown(
                    f"""
                    <div style="font-size: 1.45rem; font-weight: 900; color: #163E2B; margin-top: 2px;">
                        ₹{price:.2f} <span style="font-size: 0.85rem; font-weight: 600; color: #526058;">/ kg · {t('direct_from_farmer_note')}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with col_order:
                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                order_qty = st.number_input(
                    t("order_qty_prompt"),
                    min_value=1.0,
                    max_value=qty,
                    value=min(5.0, qty),
                    step=1.0,
                    key=f"c_qty_inp_{p_id}_{idx}",
                )
                est_total = order_qty * price
                st.metric(t("total_price"), f"₹{est_total:,.2f}")

                btn_ord1, btn_ord2 = st.columns(2)
                with btn_ord1:
                    if st.button(f"🛒 {t('btn_order_produce')}", key=f"btn_ord_{p_id}_{idx}", type="primary", use_container_width=True):
                        st.session_state.consumer_confirming_order = {
                            "produce_id": p_id,
                            "farmer_id": farmer_id,
                            "farmer_name": farmer_name_str,
                            "crop": crop,
                            "grade": grade,
                            "quantity_kg": order_qty,
                            "price_per_kg": price,
                            "total_value": est_total,
                            "location": loc,
                            "district": dist,
                        }
                        st.rerun()
                with btn_ord2:
                    is_viewing = (st.session_state.get("consumer_active_view_lot_id") == p_id)
                    view_btn_txt = t("btn_hide_lot") if is_viewing else t("btn_view_lot")
                    if st.button(f"👁 {view_btn_txt}", key=f"btn_v_{p_id}_{idx}", use_container_width=True):
                        st.session_state.consumer_active_view_lot_id = None if is_viewing else p_id
                        st.rerun()

            # Expanded Product Details Card
            if st.session_state.get("consumer_active_view_lot_id") == p_id:
                st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
                with st.container(border=True):
                    st.subheader(f"📋 {t('product_details_title')} — #{p_id}")
                    
                    p_col1, p_col2 = st.columns(2)
                    with p_col1:
                        st.markdown(f"**🌾 {t('produce_label')}:** {crop} (Grade {grade})")
                        st.markdown(f"**👨‍🌾 {t('farmer_label')}:** {farmer_name_str} (#{farmer_id})")
                        st.markdown(f"**📍 {t('farm_source_label')}:** {loc}, {dist}")
                    with p_col2:
                        st.markdown(f"**💰 {t('price_label')}:** ₹{price:.2f}/kg")
                        st.markdown(f"**📦 {t('available_qty_label')}:** {qty:,.0f} kg")
                        st.markdown(f"**📅 {t('harvested_date')}:** {h_date}")
                    
                    st.caption("✓ Tested for quality compliance. Directly dispatched from farm orchard.")

st.divider()

# ============================================================
# 7. CONSUMER ORDER HISTORY & TRACKING
# ============================================================

st.subheader(f"📦 {t('consumer_my_orders_title')}")

if consumer_orders.empty:
    render_empty_state(
        t("no_consumer_orders_title"),
        t("no_consumer_orders_desc"),
        t("no_consumer_orders_action"),
    )
else:
    for _, o in consumer_orders.sort_values("date", ascending=False).iterrows():
        ord_id = str(o["order_id"])
        c_status = str(o["status"])
        c_crop = str(o["crop"])
        c_qty = float(o["quantity_kg"])
        c_rate = float(o["price_per_kg"])
        c_total = float(o["total_value"])
        c_date = str(o["date"])
        c_farmer_id = str(o["farmer_id"])

        status_color = "#176536" if c_status in ["Delivered", "Completed"] else (
            "#1952B3" if c_status == "In Transit" else (
                "#163E2B" if c_status == "Confirmed" else "#E8B83D"
            )
        )
        status_key = f"status_{c_status.lower().replace(' ', '_')}"
        status_text = t(status_key)

        with st.container(border=True):
            col_o1, col_o2, col_o3 = st.columns([2.2, 2.2, 1.6])
            with col_o1:
                st.markdown(f"### 🛍️ {t('order_number', order_id=ord_id)}")
                st.write(f"**{t('commodity')}:** {crop_icons.get(c_crop.lower(), '🌱')} {c_crop} ({c_qty:,.0f} kg)")
                st.write(f"{t('farmer_id_input')}: **{c_farmer_id}**")
            with col_o2:
                st.write(f"**{t('total_deal_val')}:** **₹{c_total:,.2f}** (@ ₹{c_rate:.2f}/kg)")
                st.markdown(f"{t('status')}: <span style='color:{status_color}; font-weight:800;'>● {status_text}</span>", unsafe_allow_html=True)
                st.caption(f"📅 {t('ordered_date')}: {c_date}")
            with col_o3:
                st.caption(f"{t('track_order_journey')}:")
                if c_status == "Order Placed":
                    st.markdown("<span style='color:#E8B83D; font-weight:700;'>⏳ Placed ➔ Confirming</span>", unsafe_allow_html=True)
                elif c_status == "Confirmed":
                    st.markdown("<span style='color:#163E2B; font-weight:700;'>✓ Confirmed ➔ Packing</span>", unsafe_allow_html=True)
                elif c_status == "In Transit":
                    st.markdown("<span style='color:#1952B3; font-weight:700;'>🚚 In Transit ➔ Doorstep</span>", unsafe_allow_html=True)
                elif c_status in ["Delivered", "Completed"]:
                    st.markdown("<span style='color:#176536; font-weight:700;'>🎉 Delivered & Settled</span>", unsafe_allow_html=True)

st.divider()
st.caption(f"ℹ️ {t('consumer_footer_caption')}")