import streamlit as st
import pandas as pd

from utils.data_loader import (
    load_farmers,
    load_buyers,
    load_produce,
    load_transactions,
)

from utils.auth import (
    initialize_auth,
    login,
    logout,
    is_logged_in,
    DEMO_USERS,
)

from utils.translations import (
    t,
    get_current_language,
    set_current_language,
    LANGUAGE_MAP,
    LANGUAGE_DISPLAY_NAMES,
)

from utils.voice_assistant import render_kisan_bol

from ui.theme import inject_custom_theme, get_logo_base64, render_sidebar_header
from ui.cinematic_hero import render_cinematic_landing
from ui.setu_components import (
    render_brand_header,
    render_glass_feature_hero,
    render_glass_auth_header,
    render_setu_pulse,
    render_setu_bridge,
    render_price_chit,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Kisan Setu | खेत से बाज़ार तक",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply 'Bharat, Reimagined' visual language with suppressed Streamlit chrome
inject_custom_theme()

# Auth Initialization
initialize_auth()


# ============================================================
# CINEMATIC FULL-SCREEN VIDEO LANDING & AUTHENTICATION
# ============================================================

def login_page():
    render_cinematic_landing()


# ============================================================
# HOME DASHBOARD
# ============================================================

def home_page():
    inject_custom_theme()

    farmers = load_farmers()
    buyers = load_buyers()
    produce = load_produce()
    transactions = load_transactions()

    user_name = st.session_state.get("user_name", "User")
    user_role = st.session_state.get("user_role", "Farmer")
    user_id = st.session_state.get("user_id", "")

    user_icon = {
        "Farmer": "👨‍🌾",
        "Buyer": "🛒",
        "Consumer": "🛍️",
        "Logistics": "🚚",
        "Admin": "🏛️",
    }.get(user_role, "👤")

    role_label_key = f"role_{user_role.lower()}"
    role_label = t(role_label_key)

    # Unified Brand Header with Official Logo
    render_brand_header(
        title=f"KISAN SETU · {role_label.upper()} HUB",
        subtitle=f"{t('welcome')}, {user_name} ({user_id}) · {t('pilot_region')}",
        badge=f"{user_icon} {role_label.upper()}",
    )

    # Dynamic benchmark average
    dynamic_avg = 38.00
    try:
        from data_ingestion.market_data import get_latest_market_price
        dynamic_avg = float(get_latest_market_price("Onion").get("modal_price_per_kg", 38.00))
    except Exception:
        pass

    # Setu Macro Pulse Ribbon
    render_setu_pulse(
        farmers_count=len(farmers),
        avg_price=dynamic_avg,
        buyers_count=len(buyers),
        fulfilment_rate=92,
    )

    # The Functional Setu Bridge Motif
    render_setu_bridge(
        left_label=t("farm_node"),
        left_sub="Nashik & Ahmednagar",
        center_label=t("bridge_match_label"),
        right_label=t("market_node"),
        right_sub="Pune & Mumbai Wholesale Centers",
    )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Role-Specific Directives & Next Actions
    st.subheader(t("what_should_do_today"))

    if user_role == "Farmer":
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, rgba(22, 62, 43, 0.05) 0%, rgba(217, 119, 6, 0.08) 100%), #FFFFFF; border: 1.5px solid rgba(22, 62, 43, 0.18); border-radius: 16px; padding: 22px 26px; margin-bottom: 1.2rem; box-shadow: 0 6px 20px rgba(22, 62, 43, 0.06);">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 12px;">
                    <div>
                        <span style="font-size: 0.72rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; background: #163E2B; color: #FFFFFF; padding: 3px 10px; border-radius: 6px;">✦ {t('what_should_do_today')}</span>
                        <div style="font-size: 1.25rem; font-weight: 800; color: #163E2B; margin-top: 6px;">
                            🧅 {t('crop_onion')} · 500 kg (Grade A)
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.35rem; font-weight: 900; color: #D97706;">₹31.00 <span style="font-size: 0.85rem; font-weight: 600; color: #526058;">/ kg</span></div>
                        <div style="font-size: 0.8rem; font-weight: 700; color: #2D6A4F;">94% {t('match_score_label')} · +₹500 {t('extra_realization')}</div>
                    </div>
                </div>
                <div style="font-size: 0.9rem; color: #4B5563; line-height: 1.6; margin-bottom: 14px; border-top: 1px solid rgba(22,62,43,0.08); padding-top: 10px;">
                    💡 <b>{t('setu_suggests')}:</b> {t('farmer_morning_rec')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_act1, col_act2, col_act3 = st.columns([1.5, 1.5, 1])
        with col_act1:
            if st.button(f"🤝 {t('nav_farmer_match')} →", use_container_width=True, type="primary"):
                st.switch_page("pages/farmer.py")
        with col_act2:
            if st.button(f"🌱 {t('nav_produce_list')} →", use_container_width=True):
                st.switch_page("pages/list_produce.py")
        with col_act3:
            if st.button(f"📦 {t('nav_active_orders')}", use_container_width=True):
                st.switch_page("pages/farmer_orders.py")

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    elif user_role == "Buyer":
        st.markdown(
            f"""
            <div style="background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(14px); border: 1px solid rgba(22, 62, 43, 0.12); border-radius: 14px; padding: 18px 22px; margin-bottom: 1rem; box-shadow: 0 4px 16px rgba(22, 62, 43, 0.04);">
                <div style="font-size: 0.98rem; font-weight: 800; color: #163E2B; margin-bottom: 8px;">
                    🛒 {t('buyer_directive_title')}:
                </div>
                <div style="font-size: 0.88rem; color: #526058; line-height: 1.6;">
                    1. <b>{t('nav_procurement')}:</b> {t('buyer_dir_step1')}<br>
                    2. <b>{t('nav_requirements')}:</b> {t('buyer_dir_step2')}<br>
                    3. <b>{t('buyer_dir_step3_title')}:</b> {t('buyer_dir_step3')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif user_role == "Consumer":
        st.markdown(
            f"""
            <div style="background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(14px); border: 1px solid rgba(22, 62, 43, 0.12); border-radius: 14px; padding: 18px 22px; margin-bottom: 1rem; box-shadow: 0 4px 16px rgba(22, 62, 43, 0.04);">
                <div style="font-size: 0.98rem; font-weight: 800; color: #163E2B; margin-bottom: 8px;">
                    🛍️ {t('consumer_directive_title')}:
                </div>
                <div style="font-size: 0.88rem; color: #526058; line-height: 1.6;">
                    1. <b>{t('consumer_dir_step1_title')}:</b> {t('consumer_dir_step1')}<br>
                    2. <b>{t('consumer_dir_step2_title')}:</b> {t('consumer_dir_step2')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif user_role == "Logistics":
        st.markdown(
            f"""
            <div style="background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(14px); border: 1px solid rgba(22, 62, 43, 0.12); border-radius: 14px; padding: 18px 22px; margin-bottom: 1rem; box-shadow: 0 4px 16px rgba(22, 62, 43, 0.04);">
                <div style="font-size: 0.98rem; font-weight: 800; color: #163E2B; margin-bottom: 8px;">
                    🚚 {t('logistics_directive_title')}:
                </div>
                <div style="font-size: 0.88rem; color: #526058; line-height: 1.6;">
                    1. <b>{t('logistics_dir_step1_title')}:</b> {t('logistics_dir_step1')}<br>
                    2. <b>{t('logistics_dir_step2_title')}:</b> {t('logistics_dir_step2')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:
        st.markdown(
            f"""
            <div style="background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(14px); border: 1px solid rgba(22, 62, 43, 0.12); border-radius: 14px; padding: 18px 22px; margin-bottom: 1rem; box-shadow: 0 4px 16px rgba(22, 62, 43, 0.04);">
                <div style="font-size: 0.98rem; font-weight: 800; color: #163E2B; margin-bottom: 8px;">
                    🏛️ {t('admin_directive_title')}:
                </div>
                <div style="font-size: 0.88rem; color: #526058; line-height: 1.6;">
                    1. <b>{t('admin_dir_step1_title')}:</b> {t('admin_dir_step1')}<br>
                    2. <b>{t('admin_dir_step2_title')}:</b> {t('admin_dir_step2')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # Logout Button
    if st.button(f"🚪 {t('logout')}", use_container_width=True):
        logout()
        st.rerun()


# ============================================================
# LOGGED OUT FLOW (POSITION="HIDDEN" TO SUPPRESS AUTO-DISCOVERY)
# ============================================================

if not is_logged_in():
    login_page_obj = st.Page(login_page, title=t("app_slogan"), icon="🌾")
    pg = st.navigation([login_page_obj], position="hidden")
    pg.run()
    st.stop()


# ============================================================
# COMPONENT DIRECTORY & REDIRECT MAP FOR PRESENTATIONS
# ============================================================

ALL_COMPONENTS = {
    f"🌾 {t('role_farmer')} — {t('nav_farmer_match')}": {"role": "F001", "path": "pages/farmer.py"},
    f"🌾 {t('role_farmer')} — {t('nav_produce_list')}": {"role": "F001", "path": "pages/list_produce.py"},
    f"📦 {t('role_farmer')} — {t('nav_active_orders')}": {"role": "F001", "path": "pages/farmer_orders.py"},
    f"📜 {t('role_farmer')} — {t('nav_schemes')}": {"role": "F001", "path": "pages/government_schemes.py"},
    f"📱 {t('role_farmer')} — {t('nav_sms_services')}": {"role": "F001", "path": "pages/sms_services.py"},
    f"🛒 {t('role_buyer')} — {t('nav_procurement')}": {"role": "B001", "path": "pages/buyer.py"},
    f"📝 {t('role_buyer')} — {t('nav_requirements')}": {"role": "B001", "path": "pages/buyer_requirements.py"},
    f"🛍️ {t('role_consumer')} — {t('nav_marketplace')}": {"role": "C001", "path": "pages/consumer.py"},
    f"🚚 {t('role_logistics')} — {t('nav_load_dispatch')}": {"role": "L001", "path": "pages/logistics.py"},
    f"🏛️ {t('role_admin')} — {t('nav_market_intel')}": {"role": "ADMIN", "path": "pages/admin_dashboard.py"},
    f"📊 {t('role_admin')} — {t('nav_impact_analytics')}": {"role": "ADMIN", "path": "pages/impact_analytics.py"},
    f"🏛️ {t('nav_digital_mandi')}": {"role": "F001", "path": "pages/digital_mandi.py"},
    f"💳 {t('nav_trade_ledger')}": {"role": "B001", "path": "pages/transactions.py"},
    f"⭐ {t('nav_feedback')}": {"role": "B001", "path": "pages/feedback.py"},
}


# ============================================================
# LOGGED-IN NAVIGATION SETUP (SORTED & GROUPED BY ROLE OR MASTER VIEW)
# ============================================================

role = st.session_state.get("user_role", "Farmer")
presentation_mode = st.session_state.get("presentation_mode", False)

if presentation_mode:
    # Master All-Access Showcase Tree (All Modules & Components)
    nav_sections = {
        f"🌾 {t('sec_farmer_eco')}": [
            st.Page(home_page, title=t("nav_farmer_overview"), icon="🏠", url_path="farmer-hub", default=(role == "Farmer")),
            st.Page("pages/farmer.py", title=t("nav_farmer_match"), icon="🤖", url_path="ai-match"),
            st.Page("pages/list_produce.py", title=t("nav_produce_list"), icon="🌾", url_path="my-produce"),
            st.Page("pages/farmer_orders.py", title=t("nav_active_orders"), icon="📦", url_path="farmer-orders"),
            st.Page("pages/government_schemes.py", title=t("nav_schemes"), icon="📜", url_path="schemes"),
            st.Page("pages/sms_services.py", title=t("nav_sms_services"), icon="📱", url_path="sms-services"),
        ],
        f"🛒 {t('sec_buyer_eco')}": [
            st.Page("pages/buyer.py", title=t("nav_procurement"), icon="🛒", url_path="procurement", default=(role == "Buyer")),
            st.Page("pages/buyer_requirements.py", title=t("nav_requirements"), icon="📝", url_path="requirements"),
        ],
        f"🛍️ {t('sec_consumer_store')}": [
            st.Page("pages/consumer.py", title=t("nav_marketplace"), icon="🛍️", url_path="marketplace", default=(role == "Consumer")),
        ],
        f"🚚 {t('sec_logistics_fleet')}": [
            st.Page("pages/logistics.py", title=t("nav_load_dispatch"), icon="🚚", url_path="dispatch", default=(role == "Logistics")),
        ],
        f"🏛️ {t('sec_state_command')}": [
            st.Page("pages/admin_dashboard.py", title=t("nav_market_intel"), icon="🏛️", url_path="market-intel", default=(role == "Admin")),
            st.Page("pages/impact_analytics.py", title=t("nav_impact_analytics"), icon="📊", url_path="impact-analytics"),
        ],
        f"🌐 {t('sec_universal_floor')}": [
            st.Page("pages/digital_mandi.py", title=t("nav_digital_mandi"), icon="🏛️", url_path="digital-mandi"),
            st.Page("pages/transactions.py", title=t("nav_trade_ledger"), icon="💳", url_path="transactions"),
            st.Page("pages/feedback.py", title=t("nav_feedback"), icon="⭐", url_path="feedback"),
        ],
    }

else:
    # Role-Specific Clean Categorized Navigation Trees
    if role == "Farmer":
        nav_sections = {
            f"🌾 {t('sec_farmer_ws')}": [
                st.Page(home_page, title=t("nav_overview_directives"), icon="🏠", url_path="dashboard", default=True),
            ],
            t("sec_my_farm"): [
                st.Page("pages/list_produce.py", title=t("nav_produce_list"), icon="🌱", url_path="my-produce"),
            ],
            t("sec_market"): [
                st.Page("pages/farmer.py", title=t("nav_farmer_match"), icon="🤝", url_path="ai-match"),
                st.Page("pages/digital_mandi.py", title=t("nav_digital_mandi"), icon="🏪", url_path="digital-mandi"),
                st.Page("pages/impact_analytics.py", title=t("sec_floor_gov"), icon="📊", url_path="market-governance"),
            ],
            t("sec_orders_delivery"): [
                st.Page("pages/farmer_orders.py", title=t("nav_active_orders"), icon="📦", url_path="farmer-orders"),
            ],
            t("sec_services"): [
                st.Page("pages/government_schemes.py", title=t("nav_schemes"), icon="🏛️", url_path="schemes"),
                st.Page("pages/sms_services.py", title=t("nav_sms_services"), icon="📱", url_path="sms-services"),
            ],
        }

    elif role == "Buyer":
        nav_sections = {
            f"🛒 {t('sec_buyer_ws')}": [
                st.Page(home_page, title=t("nav_overview_directives"), icon="🏠", url_path="dashboard", default=True),
                st.Page("pages/buyer.py", title=t("nav_procurement"), icon="🛒", url_path="procurement"),
                st.Page("pages/buyer_requirements.py", title=t("nav_requirements"), icon="📝", url_path="requirements"),
            ],
            f"🏛️ {t('sec_floor_ledger')}": [
                st.Page("pages/digital_mandi.py", title=t("nav_digital_mandi"), icon="🏛️", url_path="digital-mandi"),
                st.Page("pages/transactions.py", title=t("nav_trade_ledger"), icon="💳", url_path="transactions"),
                st.Page("pages/feedback.py", title=t("nav_feedback"), icon="⭐", url_path="feedback"),
            ],
        }

    elif role == "Consumer":
        nav_sections = {
            f"🛍️ {t('sec_consumer_store')}": [
                st.Page(home_page, title=t("nav_overview_directives"), icon="🏠", url_path="dashboard", default=True),
                st.Page("pages/consumer.py", title=t("nav_marketplace"), icon="🛍️", url_path="marketplace"),
            ],
            f"🏛️ {t('sec_floor_trust')}": [
                st.Page("pages/digital_mandi.py", title=t("nav_digital_mandi"), icon="🏛️", url_path="digital-mandi"),
                st.Page("pages/feedback.py", title=t("nav_feedback"), icon="⭐", url_path="feedback"),
            ],
        }

    elif role == "Logistics":
        nav_sections = {
            f"🚚 {t('sec_logistics_fleet')}": [
                st.Page(home_page, title=t("nav_overview_directives"), icon="🏠", url_path="dashboard", default=True),
                st.Page("pages/logistics.py", title=t("nav_load_dispatch"), icon="🚚", url_path="dispatch"),
            ],
            f"🏛️ {t('sec_floor_records')}": [
                st.Page("pages/digital_mandi.py", title=t("nav_digital_mandi"), icon="🏛️", url_path="digital-mandi"),
                st.Page("pages/transactions.py", title=t("nav_freight_settle"), icon="💳", url_path="transactions"),
            ],
        }

    else:  # Admin
        nav_sections = {
            f"🏛️ {t('sec_state_command')}": [
                st.Page(home_page, title=t("nav_executive_overview"), icon="🏠", url_path="dashboard", default=True),
                st.Page("pages/admin_dashboard.py", title=t("nav_market_intel"), icon="🏛️", url_path="market-intel"),
                st.Page("pages/impact_analytics.py", title=t("nav_impact_analytics"), icon="📊", url_path="impact-analytics"),
            ],
            f"🌐 {t('sec_net_ops')}": [
                st.Page("pages/digital_mandi.py", title=t("nav_digital_mandi"), icon="🏛️", url_path="digital-mandi"),
                st.Page("pages/transactions.py", title=t("nav_trade_ledger"), icon="💳", url_path="transactions"),
                st.Page("pages/feedback.py", title=t("nav_feedback"), icon="⭐", url_path="feedback"),
            ],
        }


# ------------------------------------------------------------
# 1. TOP SIDEBAR: LOGO, GLOBAL SETTINGS & USER SESSION CARD
# ------------------------------------------------------------

with st.sidebar:
    top_container = st.container()
    with top_container:
        st.markdown('<div id="kisan-setu-sidebar-top-marker"></div>', unsafe_allow_html=True)
        # 1. KISAN SETU Logo & Subtitle
        render_sidebar_header()

        # 2. Global Multilingual Language Selector
        current_lang = get_current_language()
        lang_options = ["English", "Marathi", "Hindi"]
        lang_labels = {
            "English": "English",
            "Marathi": "मराठी (Marathi)",
            "Hindi": "हिन्दी (Hindi)",
        }
        
        selected_lang = st.selectbox(
            t("select_language"),
            options=lang_options,
            index=lang_options.index(current_lang) if current_lang in lang_options else 0,
            format_func=lambda x: lang_labels.get(x, x),
            key="global_language_selector",
        )
        
        if selected_lang != current_lang:
            set_current_language(selected_lang)
            st.rerun()

        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

        # 3. Current Active Session Card
        user_name = st.session_state.get("user_name", "User")
        user_role = st.session_state.get("user_role", "")
        user_id = st.session_state.get("user_id", "")
        role_disp = t(f"role_{user_role.lower()}") if user_role else ""

        st.markdown(
            f"""
            <div style="background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border: 1px solid rgba(22, 62, 43, 0.14); border-radius: 12px; padding: 10px 14px; margin-bottom: 8px; box-shadow: 0 2px 8px rgba(22, 62, 43, 0.04);">
                <div style="font-size: 0.65rem; color: #526058; text-transform: uppercase; font-weight: 800; letter-spacing: 0.06em;">{t('active_session')}</div>
                <div style="font-size: 0.95rem; font-weight: 800; color: #163E2B; margin-top: 2px;">{user_name}</div>
                <div style="font-size: 0.78rem; color: #2D6A4F; font-weight: 700;">{role_disp} · <code>{user_id}</code></div>
            </div>
            <hr style="margin: 8px 0 4px 0; border: none; border-top: 1px solid rgba(22, 62, 43, 0.12);" />
            """,
            unsafe_allow_html=True,
        )


# ------------------------------------------------------------
# 2. PRIMARY NAVIGATION EXECUTION (POSITION="SIDEBAR")
# ------------------------------------------------------------

target_page = st.session_state.pop("target_page_path", None)

pg = st.navigation(nav_sections, position="sidebar", expanded=True)


# ------------------------------------------------------------
# 3. BOTTOM SIDEBAR: KISAN BOL, PRESENTATION NAVIGATOR & LOGOUT
# ------------------------------------------------------------

with st.sidebar:
    bottom_container = st.container()
    with bottom_container:
        st.markdown('<div id="kisan-setu-sidebar-bottom-marker"></div>', unsafe_allow_html=True)
        st.markdown('<hr style="margin: 6px 0 12px 0; border: none; border-top: 1px solid rgba(22, 62, 43, 0.12);" />', unsafe_allow_html=True)

        # 🎙️ KISAN BOL DEDICATED ASSISTANT PANEL
        with st.expander(f"🎙️ {t('kisan_bol_title')}", expanded=False):
            render_kisan_bol(user_role=user_role, user_profile=st.session_state)

        # ⚡ PRESENTATION & COMPONENT NAVIGATOR
        with st.expander(f"⚡ {t('presentation_nav_title')}", expanded=False):
            st.caption(t("presentation_nav_caption"))
            
            master_view = st.toggle(
                f"🌐 {t('presentation_master_toggle')}", 
                value=st.session_state.get("presentation_mode", False),
                help=t("presentation_master_help"),
                key="presentation_toggle_switch"
            )
            if master_view != st.session_state.get("presentation_mode", False):
                st.session_state["presentation_mode"] = master_view
                st.rerun()

            st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
            selected_component = st.selectbox(
                t("quick_jump_label"),
                options=list(ALL_COMPONENTS.keys()),
                index=0,
                label_visibility="collapsed"
            )
            if st.button(f"🚀 {t('quick_jump_btn')}", use_container_width=True):
                comp_info = ALL_COMPONENTS[selected_component]
                st.session_state["user_role"] = comp_info["role"]
                st.session_state["target_page_path"] = comp_info["path"]
                st.rerun()

        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

        # 🚪 LOGOUT BUTTON
        if st.button(t("logout"), use_container_width=True, key="sidebar_logout_btn"):
            logout()
            st.rerun()


# ------------------------------------------------------------
# 4. RUN PAGE DISPATCH OR REDIRECT
# ------------------------------------------------------------

if target_page:
    try:
        st.switch_page(target_page)
    except Exception:
        pg.run()
else:
    pg.run()