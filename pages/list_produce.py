"""
List Your Produce & Harvest Lots | Kisan Setu
Theme: 'Bharat, Reimagined'
Generates Farm Passport, Product Photos & AI-Assisted Quality Verification
Supports: View, Edit, Delete (with active transaction protection), and Photo Uploads.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date, datetime

from ai.quality_assistance import (
    analyze_produce_quality,
    demo_quality_assessment,
)
from utils.translations import t, get_current_language
from ui.theme import inject_custom_theme
from ui.setu_components import (
    render_brand_header,
    render_bharat_market_pulse,
    render_farm_passport,
    render_html,
)

# ============================================================
# THEME INJECTION
# ============================================================

inject_custom_theme()

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
UPLOAD_DIR = ASSETS_DIR / "uploads"

DATA_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

PRODUCE_FILE = DATA_DIR / "produce.csv"
TRANSACTIONS_FILE = DATA_DIR / "transactions.csv"

language = get_current_language()

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

if "produce_view_mode" not in st.session_state:
    st.session_state["produce_view_mode"] = "list"  # "list", "view", "edit"

if "selected_produce_id" not in st.session_state:
    st.session_state["selected_produce_id"] = None

if "delete_confirm_produce_id" not in st.session_state:
    st.session_state["delete_confirm_produce_id"] = None

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_produce_photos(produce_id: str) -> list[Path]:
    """Finds all existing product photos for a harvest lot."""
    if not produce_id:
        return []
    pid_str = str(produce_id).strip()
    photos = []
    
    # Check directory assets/uploads/{produce_id}
    pid_dir = UPLOAD_DIR / pid_str
    if pid_dir.exists() and pid_dir.is_dir():
        for f in pid_dir.iterdir():
            if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                photos.append(f)
    
    # Check direct files assets/uploads/{produce_id}_*.ext or {produce_id}.*
    if not photos and UPLOAD_DIR.exists():
        for f in UPLOAD_DIR.iterdir():
            if f.is_file() and (f.name.startswith(f"{pid_str}_") or f.stem == pid_str) and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                photos.append(f)
                
    return sorted(photos)


def check_active_transactions(produce_id: str) -> tuple[bool, list[dict]]:
    """
    Checks if lot is linked to an active transaction.
    Active statuses: 'Order Placed', 'Confirmed', 'In Transit', 'Pending'.
    """
    if not TRANSACTIONS_FILE.exists():
        return False, []
    try:
        df_tx = pd.read_csv(TRANSACTIONS_FILE)
        if df_tx.empty or "produce_id" not in df_tx.columns:
            return False, []
        
        lot_txs = df_tx[df_tx["produce_id"].astype(str).str.strip() == str(produce_id).strip()]
        if lot_txs.empty:
            return False, []
        
        active_statuses = {"order placed", "confirmed", "in transit", "pending"}
        active_txs = lot_txs[lot_txs["status"].astype(str).str.strip().str.lower().isin(active_statuses)]
        
        if not active_txs.empty:
            return True, active_txs.to_dict(orient="records")
        return False, []
    except Exception:
        return False, []


def load_produce_data() -> pd.DataFrame:
    """Loads produce dataframe safely."""
    if PRODUCE_FILE.exists():
        try:
            return pd.read_csv(PRODUCE_FILE)
        except Exception:
            pass
    return pd.DataFrame(
        columns=[
            "produce_id", "farmer_id", "crop", "quantity_kg",
            "quality_grade", "location", "district",
            "available_date", "expected_price_per_kg", "status"
        ]
    )

# ============================================================
# HEADER & MARKET PULSE
# ============================================================

render_bharat_market_pulse()

render_brand_header(
    title=t("brand_list_produce_title"),
    subtitle=t("brand_list_produce_sub"),
    badge=t("badge_lot_gen"),
)

# Current farmer profile context
current_user_name = st.session_state.get("user_name", "Ramesh Patil")
current_user_id = st.session_state.get("user_id", "F001")
if not str(current_user_id).startswith("F"):
    current_user_id = "F001"

produce_df = load_produce_data()

# ============================================================
# ROUTING: VIEW / EDIT / LIST
# ============================================================

view_mode = st.session_state.get("produce_view_mode", "list")
selected_id = st.session_state.get("selected_produce_id", None)

# ------------------------------------------------------------
# 1. VIEW HARVEST LOT DETAIL [ 👁 VIEW ]
# ------------------------------------------------------------
if view_mode == "view" and selected_id:
    lot_match = produce_df[produce_df["produce_id"].astype(str).str.strip() == str(selected_id).strip()]
    
    if lot_match.empty:
        st.warning(f"Lot #{selected_id} not found.")
        if st.button(t("back_to_lots")):
            st.session_state["produce_view_mode"] = "list"
            st.session_state["selected_produce_id"] = None
            st.rerun()
    else:
        lot = lot_match.iloc[0]
        
        top_col1, top_col2 = st.columns([1, 4])
        with top_col1:
            if st.button(t("back_to_lots"), use_container_width=True):
                st.session_state["produce_view_mode"] = "list"
                st.session_state["selected_produce_id"] = None
                st.rerun()
        with top_col2:
            st.subheader(f"🌾 {t('lot_details_title')} — #{lot['produce_id']}")
        
        st.divider()
        
        col_left, col_right = st.columns([1, 2])
        
        with col_left:
            photos = get_produce_photos(lot["produce_id"])
            if photos:
                st.image(str(photos[0]), caption=f"{lot['crop']} (#{lot['produce_id']})", use_container_width=True)
                if len(photos) > 1:
                    st.caption(f"📸 {len(photos)} {t('existing_photos_label')}")
                    sub_cols = st.columns(min(len(photos) - 1, 3))
                    for idx, p in enumerate(photos[1:4]):
                        with sub_cols[idx]:
                            st.image(str(p), use_container_width=True)
            else:
                placeholder_html = f"""
                <div style="background: rgba(244, 246, 240, 0.95); border: 1px dashed #c2c9bb; border-radius: 12px; height: 200px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #556052; text-align: center; padding: 12px; margin-bottom: 15px;">
                    <span style="font-size: 36px; line-height: 1;">📷</span>
                    <span style="font-size: 13px; font-weight: 600; margin-top: 8px; line-height: 1.3;">{t('no_product_photo')}</span>
                </div>
                """
                render_html(placeholder_html)
            
            # Status Badge & Specs
            st.markdown(f"**{t('status')}:** `{lot.get('status', 'Available')}`")
            st.markdown(f"**{t('declared_grade')}:** Grade {lot.get('quality_grade', 'A')}")
            st.markdown(f"**{t('available_date_input')}:** {lot.get('available_date', date.today())}")

        with col_right:
            m1, m2, m3 = st.columns(3)
            qty = float(lot.get("quantity_kg", 0))
            price = float(lot.get("expected_price_per_kg", 0))
            m1.metric(t("batch_commodity"), str(lot.get("crop", "")))
            m2.metric(t("batch_volume"), f"{qty:,.0f} kg")
            m3.metric(t("reservation_rate"), f"₹{price:.2f}/kg")
            
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            
            # Render Farm Passport
            district_val = str(lot.get("district", "Nashik"))
            loc_val = str(lot.get("location", "Niphad"))
            render_farm_passport(
                farmer_name=current_user_name,
                location=f"{loc_val}, {district_val}",
                crop=str(lot.get("crop", "")),
                harvest_date=str(lot.get("available_date", date.today())),
                grade=str(lot.get("quality_grade", "A")),
                match_score=94,
                logistics_route=f"{district_val} ➔ Highway Aggregation Hub",
            )
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            
            # Action button row inside detail view
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                if st.button(f"✏️ {t('edit')} #{lot['produce_id']}", use_container_width=True):
                    st.session_state["produce_view_mode"] = "edit"
                    st.rerun()
            with b_col2:
                if st.button(f"🗑 {t('delete')} #{lot['produce_id']}", type="secondary", use_container_width=True):
                    st.session_state["delete_confirm_produce_id"] = str(lot["produce_id"])
                    st.session_state["produce_view_mode"] = "list"
                    st.rerun()

# ------------------------------------------------------------
# 2. EDIT HARVEST LOT [ ✏️ EDIT ]
# ------------------------------------------------------------
elif view_mode == "edit" and selected_id:
    lot_match = produce_df[produce_df["produce_id"].astype(str).str.strip() == str(selected_id).strip()]
    
    if lot_match.empty:
        st.warning(f"Lot #{selected_id} not found.")
        if st.button(t("back_to_lots")):
            st.session_state["produce_view_mode"] = "list"
            st.session_state["selected_produce_id"] = None
            st.rerun()
    else:
        lot = lot_match.iloc[0]
        
        top_col1, top_col2 = st.columns([1, 4])
        with top_col1:
            if st.button(t("back_to_lots"), use_container_width=True):
                st.session_state["produce_view_mode"] = "list"
                st.session_state["selected_produce_id"] = None
                st.rerun()
        with top_col2:
            st.subheader(f"✏️ {t('edit_harvest_lot')} — #{lot['produce_id']}")
        
        st.divider()
        
        edit_col1, edit_col2 = st.columns(2)
        
        crop_options = ["Onion", "Tomato", "Potato", "Wheat", "Rice", "Other"]
        cur_crop = str(lot.get("crop", "Onion"))
        crop_idx = crop_options.index(cur_crop) if cur_crop in crop_options else 0
        
        with edit_col1:
            e_crop = st.selectbox(t("crop_input"), crop_options, index=crop_idx, key="edit_crop")
            e_qty = st.number_input(
                t("quantity_kg_input"),
                min_value=1,
                max_value=100000,
                value=int(float(lot.get("quantity_kg", 500))),
                step=50,
                key="edit_qty"
            )
            
            grade_options = ["A", "B", "C"]
            cur_grade = str(lot.get("quality_grade", "A")).upper()
            grade_idx = grade_options.index(cur_grade) if cur_grade in grade_options else 0
            e_grade = st.selectbox(t("grade_input"), grade_options, index=grade_idx, key="edit_grade")

        location_options = [
            "Niphad",
            "Lasalgaon",
            "Dindori",
            "Rahata",
            "Sangamner",
            "Kopargaon",
            "Ahmednagar",
            "Nashik",
        ]
        cur_loc = str(lot.get("location", "Niphad"))
        loc_idx = location_options.index(cur_loc) if cur_loc in location_options else 0

        with edit_col2:
            e_loc = st.selectbox(t("location_input"), location_options, index=loc_idx, key="edit_loc")
            
            try:
                date_val = datetime.strptime(str(lot.get("available_date", "")).strip(), "%Y-%m-%d").date()
            except Exception:
                date_val = date.today()
                
            e_date = st.date_input(t("available_date_input"), value=date_val, key="edit_date")
            
            e_price = st.number_input(
                t("expected_price_input"),
                min_value=1.0,
                max_value=1000.0,
                value=float(lot.get("expected_price_per_kg", 28.0)),
                step=1.0,
                key="edit_price"
            )

        nashik_locations = ["Niphad", "Lasalgaon", "Dindori", "Nashik"]
        e_district = "Nashik" if e_loc in nashik_locations else "Ahmednagar"
        
        st.divider()
        st.subheader(f"📷 {t('existing_photos_label')}")
        
        existing_photos = get_produce_photos(lot["produce_id"])
        if existing_photos:
            p_cols = st.columns(min(len(existing_photos), 4))
            for i, photo_path in enumerate(existing_photos):
                with p_cols[i % len(p_cols)]:
                    st.image(str(photo_path), caption=photo_path.name, use_container_width=True)
        else:
            st.caption(f"ℹ️ {t('no_product_photo')}")

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        st.subheader(f"📤 {t('upload_new_photo_label')}")
        
        uploaded_edit_files = st.file_uploader(
            t("upload_photos_label"),
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            key="edit_lot_photos",
        )
        
        farmer_edit_notes = st.text_area(
            t("farmer_notes_label"),
            placeholder=t("farmer_notes_placeholder"),
            height=70,
            key="edit_notes",
        )
        
        if uploaded_edit_files:
            if st.button(f"🔍 {t('btn_run_quality_screening')}", key="edit_qa_btn", use_container_width=True):
                first_img = uploaded_edit_files[0]
                with st.spinner(t("analyzing_image_spinner")):
                    ai_res = analyze_produce_quality(
                        image_bytes=first_img.getvalue(),
                        crop=e_crop,
                        farmer_quality=e_grade,
                        farmer_notes=farmer_edit_notes,
                        language=language,
                        mime_type=first_img.type,
                    )
                if ai_res.get("success"):
                    st.success(f"✅ {t('ai_quality_complete')}")
                    st.info(ai_res["result"])
                else:
                    demo_res = demo_quality_assessment(
                        crop=e_crop,
                        farmer_quality=e_grade,
                        farmer_notes=farmer_edit_notes,
                        language=language,
                    )
                    st.warning(f"⚠️ {t('ai_quality_fallback')}")
                    st.info(demo_res)
        
        st.divider()
        
        save_col1, save_col2 = st.columns(2)
        with save_col1:
            if st.button(f"💾 {t('save_changes')}", type="primary", use_container_width=True):
                try:
                    # Update row in produce.csv without changing produce_id or duplicating
                    mask = produce_df["produce_id"].astype(str).str.strip() == str(lot["produce_id"]).strip()
                    produce_df.loc[mask, "crop"] = e_crop
                    produce_df.loc[mask, "quantity_kg"] = e_qty
                    produce_df.loc[mask, "quality_grade"] = e_grade
                    produce_df.loc[mask, "location"] = e_loc
                    produce_df.loc[mask, "district"] = e_district
                    produce_df.loc[mask, "available_date"] = e_date.strftime("%Y-%m-%d")
                    produce_df.loc[mask, "expected_price_per_kg"] = e_price
                    
                    produce_df.to_csv(PRODUCE_FILE, index=False)
                    
                    # Save new photos if uploaded
                    if uploaded_edit_files:
                        lot_upload_dir = UPLOAD_DIR / str(lot["produce_id"]).strip()
                        lot_upload_dir.mkdir(parents=True, exist_ok=True)
                        for idx, uf in enumerate(uploaded_edit_files, start=1):
                            ext = Path(uf.name).suffix.lower()
                            with open(lot_upload_dir / f"photo_{idx}{ext}", "wb") as f:
                                f.write(uf.getvalue())
                                
                    st.success(t("changes_saved"))
                    st.session_state["produce_view_mode"] = "list"
                    st.session_state["selected_produce_id"] = None
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error saving changes: {ex}")
                    
        with save_col2:
            if st.button(t("cancel"), use_container_width=True):
                st.session_state["produce_view_mode"] = "list"
                st.session_state["selected_produce_id"] = None
                st.rerun()

# ------------------------------------------------------------
# 3. LIST / CREATE MODE (DEFAULT)
# ------------------------------------------------------------
else:
    # Top Tabs: My Harvest Lots vs Create New Lot
    tab_lots, tab_create = st.tabs([
        f"🌾 {t('my_harvest_lots')}",
        f"➕ {t('btn_create_new_lot')}",
    ])

    # ========================================================
    # TAB 1: MY HARVEST LOTS (CARDS + VIEW/EDIT/DELETE)
    # ========================================================
    with tab_lots:
        # Check if deletion confirmation dialog is triggered
        del_pid = st.session_state.get("delete_confirm_produce_id")
        if del_pid:
            del_matches = produce_df[produce_df["produce_id"].astype(str).str.strip() == str(del_pid).strip()]
            if not del_matches.empty:
                del_lot = del_matches.iloc[0]
                has_active, active_txs = check_active_transactions(del_pid)
                
                with st.container(border=True):
                    if has_active:
                        st.error(f"⚠️ **{t('cannot_delete')}**: {t('active_transaction_warn')}")
                        st.caption(f"Linked Active Orders: {len(active_txs)} | Status: {active_txs[0].get('status', 'Active')}")
                        if st.button(f"✕ {t('cancel')}", use_container_width=True):
                            st.session_state["delete_confirm_produce_id"] = None
                            st.rerun()
                    else:
                        st.warning(f"⚠️ **{t('confirm_deletion_title')}**")
                        st.markdown(
                            t(
                                "crop_quantity_summary",
                                crop=del_lot.get("crop", "Unknown"),
                                qty=f"{float(del_lot.get('quantity_kg', 0)):,.0f}",
                                lot_id=del_pid,
                            )
                        )
                        st.markdown(f"*{t('confirm_deletion_warning')}*")
                        
                        dc1, dc2 = st.columns(2)
                        with dc1:
                            if st.button(f"🗑 {t('delete_lot_btn')}", type="primary", use_container_width=True):
                                # Remove row from produce_df
                                produce_df = produce_df[produce_df["produce_id"].astype(str).str.strip() != str(del_pid).strip()]
                                produce_df.to_csv(PRODUCE_FILE, index=False)
                                st.session_state["delete_confirm_produce_id"] = None
                                st.success(t("lot_deleted", lot_id=del_pid))
                                st.rerun()
                        with dc2:
                            if st.button(t("cancel"), use_container_width=True):
                                st.session_state["delete_confirm_produce_id"] = None
                                st.rerun()
            st.divider()

        # Farmer Lots Filtering
        farmer_lots = produce_df[
            produce_df["farmer_id"].astype(str).str.strip().str.upper() == str(current_user_id).strip().upper()
        ]
        
        # If no lots for this specific farmer, show all lots or fallback gracefully
        if farmer_lots.empty and not produce_df.empty:
            display_lots = produce_df
        else:
            display_lots = farmer_lots

        # Metrics Bar (KPI Cards with localized labels and large values)
        total_lots = len(display_lots)
        total_vol = float(display_lots["quantity_kg"].sum()) if not display_lots.empty else 0
        est_val = float((display_lots["quantity_kg"] * display_lots["expected_price_per_kg"]).sum()) if not display_lots.empty else 0
        top_crop_val = display_lots["crop"].mode()[0] if not display_lots.empty and not display_lots["crop"].empty else "Onion"

        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric(t("active_lots_label"), f"{total_lots}")
        m_col2.metric(t("available_volume_label"), f"{total_vol:,.0f} kg")
        m_col3.metric(t("top_crop_label"), top_crop_val)
        m_col4.metric(t("best_opportunity_label"), f"₹{est_val:,.0f}")

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # Filters Row
        f_col1, f_col2 = st.columns([1, 2])
        with f_col1:
            unique_crops = [t("all_crops")] + sorted(list(display_lots["crop"].dropna().unique())) if not display_lots.empty else [t("all_crops")]
            selected_crop_filter = st.selectbox(f"🔍 {t('filter_by_crop')}", unique_crops, index=0)
        with f_col2:
            search_query = st.text_input(f"🔎 {t('search')}", placeholder=t("search_lots_placeholder"))

        # Apply Filters
        filtered_df = display_lots.copy()
        if selected_crop_filter != t("all_crops"):
            filtered_df = filtered_df[filtered_df["crop"] == selected_crop_filter]
        if search_query.strip():
            sq = search_query.strip().lower()
            filtered_df = filtered_df[
                filtered_df["produce_id"].astype(str).str.lower().str.contains(sq) |
                filtered_df["crop"].astype(str).str.lower().str.contains(sq) |
                filtered_df["location"].astype(str).str.lower().str.contains(sq) |
                filtered_df["district"].astype(str).str.lower().str.contains(sq)
            ]

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        if filtered_df.empty:
            st.info(f"🌾 {t('add_produce_prompt')}")
        else:
            for _, row in filtered_df.iterrows():
                pid = str(row["produce_id"]).strip()
                crop_name = str(row["crop"])
                qty_val = float(row.get("quantity_kg", 0))
                price_val = float(row.get("expected_price_per_kg", 0))
                grade_val = str(row.get("quality_grade", "A"))
                loc_name = str(row.get("location", "Niphad"))
                dist_name = str(row.get("district", "Nashik"))
                avail_date = str(row.get("available_date", "2026-09-10"))
                status_val = str(row.get("status", "Available"))

                photos = get_produce_photos(pid)

                with st.container(border=True):
                    card_col_img, card_col_info = st.columns([1, 3])

                    with card_col_img:
                        if photos:
                            st.image(str(photos[0]), use_container_width=True)
                        else:
                            placeholder_card_html = f"""
                            <div style="background: rgba(244, 246, 240, 0.95); border: 1px dashed #c2c9bb; border-radius: 8px; height: 110px; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #556052; text-align: center; padding: 6px;">
                                <span style="font-size: 24px; line-height: 1;">📷</span>
                                <span style="font-size: 11px; font-weight: 600; margin-top: 4px; line-height: 1.2;">{t('no_product_photo')}</span>
                            </div>
                            """
                            render_html(placeholder_card_html)

                    with card_col_info:
                        # Title row with Badge and ID
                        header_html = f"""
                        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 6px;">
                            <div style="font-size: 1.15rem; font-weight: 800; color: #163E2B;">
                                🌾 {crop_name} <span style="font-size: 0.85rem; color: #667085; font-weight: 600;">#{pid}</span>
                            </div>
                            <div style="display: flex; gap: 6px;">
                                <span style="background: #E8F5E9; color: #1E4620; font-weight: 700; font-size: 0.72rem; padding: 3px 8px; border-radius: 6px; border: 1px solid #A5D6A7;">
                                    GRADE {grade_val}
                                </span>
                                <span style="background: #E0F2FE; color: #0369A1; font-weight: 700; font-size: 0.72rem; padding: 3px 8px; border-radius: 6px; border: 1px solid #BAE6FD;">
                                    {status_val.upper()}
                                </span>
                            </div>
                        </div>
                        """
                        render_html(header_html)

                        # Metadata line
                        info_html = f"""
                        <div style="display: flex; flex-wrap: wrap; gap: 14px; font-size: 0.85rem; color: #374151; margin-bottom: 8px;">
                            <span>⚖️ <strong>{qty_val:,.0f} kg</strong></span>
                            <span>💰 <strong>₹{price_val:.2f}/kg</strong> (₹{qty_val * price_val:,.0f})</span>
                            <span>📍 <strong>{loc_name}, {dist_name}</strong></span>
                            <span>📅 <strong>{avail_date}</strong></span>
                        </div>
                        """
                        render_html(info_html)

                        # AI Market Match preview (prominent match %, secondary spread)
                        match_pill_html = f"""
                        <div style="background: rgba(22, 62, 43, 0.06); border: 1px solid rgba(22, 62, 43, 0.16); border-radius: 8px; padding: 6px 12px; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span style="font-weight: 800; color: #163E2B; font-size: 0.84rem;">🤝 {t('ai_match_badge')}:</span>
                                <span style="background: #163E2B; color: #FFFFFF; font-weight: 800; font-size: 0.78rem; padding: 2px 8px; border-radius: 9999px;">94% MATCH</span>
                                <span style="font-size: 0.80rem; color: #374151; font-weight: 600;">(Pune Wholesaler)</span>
                            </div>
                            <div style="font-size: 0.80rem; font-weight: 700; color: #2D6A4F;">
                                +₹2.60/kg {t('potential_spread')}
                            </div>
                        </div>
                        """
                        render_html(match_pill_html)

                        # Action Buttons
                        btn_col1, btn_col2, btn_col3 = st.columns(3)
                        with btn_col1:
                            if st.button(f"👁 {t('view')}", key=f"btn_view_{pid}", use_container_width=True):
                                st.session_state["produce_view_mode"] = "view"
                                st.session_state["selected_produce_id"] = pid
                                st.rerun()
                        with btn_col2:
                            if st.button(f"✏️ {t('edit')}", key=f"btn_edit_{pid}", use_container_width=True):
                                st.session_state["produce_view_mode"] = "edit"
                                st.session_state["selected_produce_id"] = pid
                                st.rerun()
                        with btn_col3:
                            if st.button(f"🗑 {t('delete')}", key=f"btn_del_{pid}", type="secondary", use_container_width=True):
                                st.session_state["delete_confirm_produce_id"] = pid
                                st.rerun()

    # ========================================================
    # TAB 2: CREATE NEW LOT
    # ========================================================
    with tab_create:
        st.subheader(f"👨‍🌾 {t('farmer_profile_title')}")

        col1, col2 = st.columns(2)

        with col1:
            farmer_id = st.text_input(
                t("farmer_id_input"),
                value=current_user_id,
                help=t("farmer_id_help"),
                key="create_farmer_id",
            )

        with col2:
            farmer_name = st.text_input(
                t("farmer_name_input"),
                value=current_user_name,
                key="create_farmer_name",
            )

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.subheader(f"🥕 {t('produce_spec_title')}")

        col1, col2 = st.columns(2)

        with col1:
            crop = st.selectbox(
                t("crop_input"),
                ["Onion", "Tomato", "Potato", "Wheat", "Rice", "Other"],
                key="create_crop",
            )

            quantity = st.number_input(
                t("quantity_kg_input"),
                min_value=1,
                max_value=100000,
                value=500,
                step=50,
                key="create_quantity",
            )

            quality = st.selectbox(
                t("grade_input"),
                ["A", "B", "C"],
                help=t("grade_input_help"),
                key="create_grade",
            )

        with col2:
            location_options = [
                "Niphad",
                "Lasalgaon",
                "Dindori",
                "Rahata",
                "Sangamner",
                "Kopargaon",
                "Ahmednagar",
                "Nashik",
            ]

            location = st.selectbox(
                t("location_input"),
                location_options,
                key="create_location",
            )

            available_date = st.date_input(
                t("available_date_input"),
                value=date.today(),
                key="create_date",
            )

            expected_price = st.number_input(
                t("expected_price_input"),
                min_value=1.0,
                max_value=1000.0,
                value=28.0,
                step=1.0,
                key="create_price",
            )

        # District assignment
        nashik_locations = ["Niphad", "Lasalgaon", "Dindori", "Nashik"]
        district = "Nashik" if location in nashik_locations else "Ahmednagar"

        # Farm Passport Live Preview
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.caption(f"✦ {t('farm_passport_preview_caption')}")
        render_farm_passport(
            farmer_name=farmer_name,
            location=f"{location}, {district}",
            crop=crop,
            harvest_date=available_date.strftime("%Y-%m-%d"),
            grade=quality,
            match_score=94,
            logistics_route=f"{district} ➔ Pune Highway Hub",
        )

        # Photos & AI Quality Screening
        st.divider()
        st.subheader(f"📷 {t('photos_ai_screening_title')}")
        st.caption(t("photos_ai_screening_caption"))

        uploaded_files = st.file_uploader(
            t("upload_photos_label"),
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            key="create_photos_uploader",
        )

        if uploaded_files:
            preview_columns = st.columns(min(len(uploaded_files), 4))
            for index, uploaded_file in enumerate(uploaded_files):
                with preview_columns[index % len(preview_columns)]:
                    st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)

        farmer_notes = st.text_area(
            t("farmer_notes_label"),
            placeholder=t("farmer_notes_placeholder"),
            height=80,
            key="create_farmer_notes",
        )

        if uploaded_files:
            if st.button(f"🔍 {t('btn_run_quality_screening')}", key="create_run_qa_btn", use_container_width=True):
                first_image = uploaded_files[0]
                image_bytes = first_image.getvalue()
                mime_type = first_image.type

                with st.spinner(t("analyzing_image_spinner")):
                    ai_response = analyze_produce_quality(
                        image_bytes=image_bytes,
                        crop=crop,
                        farmer_quality=quality,
                        farmer_notes=farmer_notes,
                        language=language,
                        mime_type=mime_type,
                    )

                if ai_response.get("success"):
                    st.success(f"✅ {t('ai_quality_complete')}")
                    st.info(ai_response["result"])
                else:
                    demo_result = demo_quality_assessment(
                        crop=crop,
                        farmer_quality=quality,
                        farmer_notes=farmer_notes,
                        language=language,
                    )
                    st.warning(f"⚠️ {t('ai_quality_fallback')}")
                    st.info(demo_result)

        # Publish Produce Listing
        st.divider()

        s1, s2, s3, s4 = st.columns(4)
        s1.metric(t("batch_commodity"), crop)
        s2.metric(t("batch_volume"), f"{quantity:,} kg")
        s3.metric(t("declared_grade"), t("grade_label", grade=quality))
        s4.metric(t("reservation_rate"), f"₹{expected_price:.2f}/kg")

        if st.button(f"🚀 {t('btn_publish_lot')} →", type="primary", use_container_width=True):
            if not farmer_id.strip():
                st.error(t("err_provide_farmer_id"))
                st.stop()
            if not farmer_name.strip():
                st.error(t("err_provide_farmer_name"))
                st.stop()

            try:
                numbers = []
                for pid in produce_df["produce_id"].astype(str):
                    try:
                        numbers.append(int(pid.replace("P", "")))
                    except ValueError:
                        pass
                next_num = max(numbers) + 1 if numbers else 1
                produce_id = f"P{next_num:03d}"

                new_produce = {
                    "produce_id": produce_id,
                    "farmer_id": farmer_id.strip(),
                    "crop": crop,
                    "quantity_kg": quantity,
                    "quality_grade": quality,
                    "location": location,
                    "district": district,
                    "available_date": available_date.strftime("%Y-%m-%d"),
                    "expected_price_per_kg": expected_price,
                    "status": "Available",
                }

                produce_df = pd.concat([produce_df, pd.DataFrame([new_produce])], ignore_index=True)
                produce_df.to_csv(PRODUCE_FILE, index=False)

                # Save photos if any
                if uploaded_files:
                    produce_upload_dir = UPLOAD_DIR / produce_id
                    produce_upload_dir.mkdir(parents=True, exist_ok=True)
                    for idx, uf in enumerate(uploaded_files, start=1):
                        ext = Path(uf.name).suffix.lower()
                        with open(produce_upload_dir / f"photo_{idx}{ext}", "wb") as f:
                            f.write(uf.getvalue())

                st.success(f"🎉 {t('produce_listed_success', lot_id=produce_id)}")
                st.rerun()

            except Exception as e:
                st.error(f"Error publishing listing: {e}")

st.divider()
st.caption(f"ℹ️ {t('produce_footer_caption')}")