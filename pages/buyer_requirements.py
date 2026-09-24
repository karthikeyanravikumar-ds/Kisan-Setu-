"""
Buyer Requirements Requisition Board | Kisan Setu
Theme: 'Bharat, Reimagined'
Enables bulk buyers and retailers to publish purchase orders and procurement lots.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date

from utils.translations import t, get_current_language
from utils.data_loader import load_buyers, load_buyer_requirements
from ui.theme import inject_custom_theme
from ui.setu_components import (
    render_brand_header,
    render_bharat_market_pulse,
    render_empty_state,
)

# =========================================================
# THEME INJECTION
# =========================================================

inject_custom_theme()
language = get_current_language()

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BUYERS_FILE = DATA_DIR / "buyers.csv"
REQUIREMENTS_FILE = DATA_DIR / "buyer_requirements.csv"

REQUIREMENT_COLUMNS = [
    "requirement_id", "buyer_id", "buyer_name", "buyer_type", "crop",
    "quantity_kg", "minimum_quality", "maximum_price_per_kg", "delivery_location",
    "required_date", "additional_requirements", "status", "posted_date"
]

render_bharat_market_pulse()

# Brand Header with Logo
render_brand_header(
    title=f"{t('brand_buyer_req_title')}",
    subtitle=t("brand_buyer_req_sub"),
    badge=t("badge_req_board"),
)

st.divider()

buyers = load_buyers()
requirements = load_buyer_requirements()

current_user_id = st.session_state.get("user_id", "B001")
if not str(current_user_id).startswith("B"):
    current_user_id = "B001"

buyer_ids = buyers["buyer_id"].tolist() if not buyers.empty else ["B001"]
default_idx = buyer_ids.index(current_user_id) if current_user_id in buyer_ids else 0

col_sel_b, col_nav_b = st.columns([2.2, 1.2])
with col_sel_b:
    selected_buyer_id = st.selectbox(
        f"🏢 {t('select_buyer_entity')}",
        buyer_ids,
        index=default_idx,
        format_func=lambda x: f"{x} · {buyers[buyers['buyer_id']==x].iloc[0]['name']} ({buyers[buyers['buyer_id']==x].iloc[0]['location']})" if not buyers.empty and x in buyers['buyer_id'].values else str(x),
    )
    if selected_buyer_id != current_user_id:
        st.session_state.user_id = selected_buyer_id
        st.rerun()

with col_nav_b:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    if st.button(f"🛒 {t('buyer_hub_header')} →", use_container_width=True, key="btn_go_to_hub"):
        st.switch_page("pages/buyer.py")

selected_buyer = buyers[buyers["buyer_id"] == selected_buyer_id].iloc[0] if not buyers.empty and selected_buyer_id in buyers["buyer_id"].values else buyers.iloc[0]

# Form
with st.form("post_requirement_form"):
    st.subheader(f"📋 {t('req_details_title')}")
    c1, c2 = st.columns(2)

    with c1:
        crop_options = ["Onion", "Tomato", "Potato", "Wheat", "Rice", "Banana", "Ginger"]
        cur_crop = str(selected_buyer.get("crop", "Onion"))
        c_idx = crop_options.index(cur_crop) if cur_crop in crop_options else 0
        crop = st.selectbox(t("crop_input"), crop_options, index=c_idx)

        quantity = st.number_input(
            t("req_volume_kg"),
            min_value=50.0,
            max_value=500000.0,
            value=float(selected_buyer.get("required_quantity_kg", 550.0)),
            step=50.0,
        )

        min_quality = st.selectbox(
            t("min_accept_grade"),
            ["A", "B", "C"],
            index=0,
        )

    with c2:
        max_price = st.number_input(
            t("max_budget_price"),
            min_value=1.0,
            max_value=500.0,
            value=float(selected_buyer.get("max_price_per_kg", 38.0)),
            step=0.5,
        )

        location = st.text_input(
            t("delivery_hub_loc"),
            value=str(selected_buyer.get("location", "Pune")),
        )

        req_date = st.date_input(
            t("target_delivery_date"),
            value=date.today(),
        )

    additional = st.text_area(
        t("packaging_quality_specs"),
        placeholder=t("packaging_placeholder"),
        height=70,
    )

    btn_f1, btn_f2 = st.columns(2)
    with btn_f1:
        submit = st.form_submit_button(f"💾 {t('save_requirement_btn')}", type="primary", use_container_width=True)
    with btn_f2:
        submit_and_match = st.form_submit_button(f"🔎 {t('btn_find_matches')} →", use_container_width=True)

if submit or submit_and_match:
    num_list = []
    for rid in requirements["requirement_id"].astype(str):
        try:
            num_list.append(int(rid.replace("R", "").replace("B", "")))
        except ValueError:
            pass
    req_id = f"R{(max(num_list) + 1 if num_list else 1):03d}"

    new_row = {
        "requirement_id": req_id,
        "buyer_id": selected_buyer["buyer_id"],
        "buyer_name": selected_buyer["name"],
        "buyer_type": selected_buyer["buyer_type"],
        "crop": crop,
        "quantity_kg": quantity,
        "minimum_quality": min_quality,
        "maximum_price_per_kg": max_price,
        "delivery_location": location.strip(),
        "required_date": req_date.strftime("%Y-%m-%d"),
        "additional_requirements": additional.strip(),
        "status": "Active",
        "posted_date": date.today().strftime("%Y-%m-%d"),
    }

    requirements = pd.concat([requirements, pd.DataFrame([new_row])], ignore_index=True)
    requirements.to_csv(REQUIREMENTS_FILE, index=False)

    # Sync buyers.csv for AI matching
    mask = buyers["buyer_id"] == selected_buyer["buyer_id"]
    nashik_locs = ["Niphad", "Lasalgaon", "Dindori", "Nashik"]
    ahmednagar_locs = ["Rahata", "Sangamner", "Kopargaon", "Ahmednagar"]
    loc_clean = location.strip()
    if loc_clean in nashik_locs:
        b_dist = "Nashik"
    elif loc_clean in ahmednagar_locs:
        b_dist = "Ahmednagar"
    elif loc_clean.lower() == "mumbai":
        b_dist = "Mumbai"
    else:
        b_dist = "Pune"

    if mask.any():
        buyers.loc[mask, "crop"] = crop
        buyers.loc[mask, "required_quantity_kg"] = quantity
        buyers.loc[mask, "min_quality"] = min_quality
        buyers.loc[mask, "max_price_per_kg"] = max_price
        buyers.loc[mask, "location"] = loc_clean
        buyers.loc[mask, "district"] = b_dist
        buyers.loc[mask, "required_date"] = req_date.strftime("%Y-%m-%d")
    else:
        new_b = {
            "buyer_id": selected_buyer["buyer_id"],
            "name": selected_buyer.get("name", "Buyer"),
            "buyer_type": selected_buyer.get("buyer_type", "Retailer"),
            "location": loc_clean,
            "district": b_dist,
            "crop": crop,
            "required_quantity_kg": quantity,
            "min_quality": min_quality,
            "max_price_per_kg": max_price,
            "required_date": req_date.strftime("%Y-%m-%d"),
        }
        buyers = pd.concat([buyers, pd.DataFrame([new_b])], ignore_index=True)

    buyers.to_csv(BUYERS_FILE, index=False)

    st.success(f"✅ {t('req_published_success', req_id=req_id)}")
    if submit_and_match:
        st.switch_page("pages/buyer.py")
    else:
        st.rerun()

st.divider()

# Active Requirements Board
st.subheader(f"📢 {t('active_reqs_board')}")

active_reqs = requirements[requirements["status"].astype(str).str.lower() == "active"]

if active_reqs.empty:
    render_empty_state(t("no_active_reqs_title"), t("no_active_reqs_desc"))
else:
    for _, r in active_reqs.sort_values("posted_date", ascending=False).iterrows():
        with st.container(border=True):
            col_a, col_b, col_c = st.columns([2.5, 2.3, 1.2])
            with col_a:
                st.markdown(f"### 🌾 {r['crop']} · {t('requisition_number', req_id=r['requirement_id'])}")
                st.write(f"{t('buyer')}: **{r['buyer_name']}** ({r['buyer_type']})")
                st.caption(f"📅 {t('target_delivery_date')}: {r['required_date']}")
            with col_b:
                st.write(f"📦 {t('volume')}: **{float(r['quantity_kg']):,.0f} kg** ({t('min_grade_label', grade=r['minimum_quality'])})")
                st.write(f"💰 {t('ceiling_rate')}: **₹{float(r['maximum_price_per_kg']):.2f}/kg** · {t('hub')}: **{r['delivery_location']}**")
                if r['additional_requirements']:
                    st.caption(f"Specs: {r['additional_requirements']}")
            with col_c:
                st.markdown(f"<span style='background:#E6F5EC; color:#176536; font-size:0.75rem; font-weight:800; padding:4px 10px; border-radius:12px;'>● {t('status_active')}</span>", unsafe_allow_html=True)
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                if st.button(f"🔎 {t('btn_find_matches')}", key=f"btn_match_req_{r['requirement_id']}", use_container_width=True):
                    # Sync buyer record to this requirement
                    b_mask = buyers["buyer_id"] == r["buyer_id"]
                    if b_mask.any():
                        buyers.loc[b_mask, "crop"] = r["crop"]
                        buyers.loc[b_mask, "required_quantity_kg"] = float(r["quantity_kg"])
                        buyers.loc[b_mask, "min_quality"] = r["minimum_quality"]
                        buyers.loc[b_mask, "max_price_per_kg"] = float(r["maximum_price_per_kg"])
                        buyers.loc[b_mask, "location"] = r["delivery_location"]
                        buyers.to_csv(BUYERS_FILE, index=False)
                    st.session_state.user_id = r["buyer_id"]
                    st.switch_page("pages/buyer.py")

st.caption(f"ℹ️ {t('buyer_req_footer')}")