"""
Kisan Setu Design System — Theme & Styling Engine
Visual Identity: Bharat, Reimagined
Colors matched with Kisan Setu Logo: Deep Neem (#163E2B), Forest (#1E5128), Leaf Accent (#2D6A4F), Haldi Gold (#D97706), Khadi Canvas (#F8F5EE)
Typography: Cinzel / Playfair Display (Serif Brand) + Plus Jakarta Sans / Manrope (Modern Tech UI) + Noto Sans Devanagari
Complete Streamlit branding removal, Glassmorphic architecture & modern authentication styling.
"""

import streamlit as st
import os
import base64

# ============================================================
# COLOR TOKENS (MATCHED WITH KISAN SETU LOGO)
# ============================================================

COLOR_NEEM = "#163E2B"           # Deep readable forest/neem from logo
COLOR_DEEP_FOREST = "#1E5128"    # Primary rich green
COLOR_LEAF_ACCENT = "#2D6A4F"    # Vibrant botanical leaf green
COLOR_EMERALD = "#388E3C"        # Indicator green
COLOR_HALDI = "#D97706"          # Warm sunlight amber from logo
COLOR_GOLD = "#F59E0B"           # Secondary gold accent
COLOR_TERRACOTTA = "#B45309"     # Earthy rust
COLOR_JOWAR = "#D7B982"          # Harvest wheat
COLOR_KHADI = "#F8F5EE"          # Clean warm canvas
COLOR_SURFACE = "#FFFDF9"        # Pristine card surface
COLOR_CARD = "#FFFFFF"           # Solid card
COLOR_INK = "#111813"            # High contrast deep charcoal text
COLOR_MUTED = "#526058"          # High readability muted slate
COLOR_BORDER = "rgba(22, 62, 43, 0.12)"
COLOR_BORDER_ACCENT = "rgba(22, 62, 43, 0.22)"


def get_logo_base64():
    """Returns base64 string for the Kisan Setu logo."""
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "kisan_setu_logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""


def inject_custom_theme():
    """
    Injects the complete 'Bharat, Reimagined' stylesheet with Glassmorphism,
    Streamlit branding suppression, high-contrast ticker, and motion gradients into Streamlit.
    """
    logo_b64 = get_logo_base64()
    
    custom_css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700;800;900&family=Manrope:wght@400;500;600;700;800&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&family=Material+Icons&family=Noto+Sans+Devanagari:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;0,800;1,600&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    :root {{
        --c-neem: #163E2B;
        --c-forest: #1E5128;
        --c-leaf: #2D6A4F;
        --c-emerald: #388E3C;
        --c-haldi: #D97706;
        --c-gold: #F59E0B;
        --c-terracotta: #B45309;
        --c-jowar: #D7B982;
        --c-khadi: #F8F5EE;
        --c-surface: #FFFDF9;
        --c-card: #FFFFFF;
        --c-card-glass: rgba(255, 255, 255, 0.82);
        --c-ink: #111813;
        --c-muted: #526058;
        --c-border: rgba(22, 62, 43, 0.12);
        --c-border-glass: rgba(255, 255, 255, 0.85);
        --c-border-accent: rgba(22, 62, 43, 0.22);
        
        --radius-sm: 10px;
        --radius-md: 16px;
        --radius-lg: 24px;
        --radius-pill: 9999px;
        
        --shadow-subtle: 0 4px 16px rgba(22, 62, 43, 0.05);
        --shadow-glass: 0 20px 40px -10px rgba(22, 62, 43, 0.08), 0 1px 3px rgba(0,0,0,0.03);
        --shadow-float: 0 16px 36px rgba(22, 62, 43, 0.12);
        
        --font-main: 'Plus Jakarta Sans', 'Manrope', 'Noto Sans Devanagari', -apple-system, sans-serif;
        --font-brand: 'Cinzel', 'Playfair Display', Georgia, serif;
    }}

    /* =======================================================
       1. STREAMLIT CHROME & COMPLETE SUPPRESSION OF COLLAPSE/EXPAND ARTIFACTS
       ======================================================= */
    header[data-testid="stHeader"] {{
        display: flex !important;
        visibility: visible !important;
        background: transparent !important;
        z-index: 99 !important;
    }}

    footer, 
    #MainMenu, 
    [data-testid="stStatusWidget"], 
    [data-testid="stToolbar"], 
    [data-testid="stDecoration"], 
    [data-testid="manage-app-button"], 
    .viewerBadge_container__1QSob, 
    .styles_viewerBadge__1A-5-,
    div[data-testid="stToolbarActions"],
    button[title="View app in Streamlit Community Cloud"],
    #GithubIcon,
    div[data-baseweb="tooltip"],
    div[data-testid="stTooltipContent"],
    div[role="tooltip"] {{
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }}

    /* Sidebar Base Styling & Guaranteed Expansion */
    section[data-testid="stSidebar"],
    div[data-testid="stSidebar"],
    aside[data-testid="stSidebar"] {{
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        transform: none !important;
        margin-left: 0 !important;
        background: linear-gradient(180deg, #FBF8F2 0%, #F4EFE6 100%) !important;
        border-right: 1px solid var(--c-border) !important;
        min-width: 290px !important;
        width: 300px !important;
        max-width: 340px !important;
        position: relative !important;
        z-index: 99 !important;
    }}

    /* Floating Collapsed Sidebar Expand Button */
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {{
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        background: rgba(255, 255, 255, 0.98) !important;
        backdrop-filter: blur(12px) !important;
        border: 1.5px solid #163E2B !important;
        border-radius: 10px !important;
        margin: 8px !important;
        box-shadow: 0 4px 16px rgba(22, 62, 43, 0.16) !important;
        color: #163E2B !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        z-index: 999999 !important;
    }}

    [data-testid="stSidebarCollapsedControl"]:hover,
    [data-testid="collapsedControl"]:hover {{
        background: #FFFFFF !important;
        border-color: #2D6A4F !important;
        box-shadow: 0 6px 22px rgba(22, 62, 43, 0.24) !important;
        transform: scale(1.08) !important;
    }}

    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="collapsedControl"] button {{
        color: #163E2B !important;
    }}

    [data-testid="stSidebarCollapsedControl"] svg,
    [data-testid="collapsedControl"] svg {{
        fill: #163E2B !important;
        stroke: #163E2B !important;
    }}

    /* Sidebar Collapse Button inside the Sidebar */
    [data-testid="stSidebarCollapseButton"] {{
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
    }}

    [data-testid="stSidebarCollapseButton"] button {{
        color: #163E2B !important;
        border-radius: 8px !important;
        transition: background 0.2s ease !important;
    }}

    [data-testid="stSidebarCollapseButton"] button:hover {{
        background: rgba(22, 62, 43, 0.08) !important;
    }}

    /* Ensure Material Symbols Icons render as proper graphical glyphs */
    [data-testid="stSidebarCollapseButton"] span,
    [data-testid="stSidebarCollapsedControl"] span,
    .material-symbols-rounded,
    .material-symbols-outlined,
    .material-icons,
    [class*="material-symbols"],
    [data-testid="stIconMaterial"],
    span[translate="no"] {{
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
        font-weight: normal !important;
        font-style: normal !important;
        font-size: 20px !important;
        line-height: 1 !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        display: inline-block !important;
        white-space: nowrap !important;
        word-wrap: normal !important;
        direction: ltr !important;
        -webkit-font-feature-settings: 'liga' !important;
        font-feature-settings: 'liga' !important;
        -webkit-font-smoothing: antialiased !important;
    }}

    /* Global Base Canvas */
    .stApp {{
        background: linear-gradient(180deg, #F9F6F0 0%, #F5F1E8 100%) !important;
        font-family: var(--font-main) !important;
        color: var(--c-ink) !important;
    }}

    /* Typography */
    h1:not(.cinematic-page-container *), 
    h2:not(.cinematic-page-container *), 
    h3:not(.cinematic-page-container *), 
    h4:not(.cinematic-page-container *), 
    h5:not(.cinematic-page-container *), 
    h6:not(.cinematic-page-container *) {{
        font-family: var(--font-main) !important;
        color: var(--c-neem) !important;
        font-weight: 800 !important;
        letter-spacing: -0.025em !important;
    }}

    h1:not(.cinematic-page-container *) {{ 
        font-family: var(--font-brand) !important; 
        font-size: 2.3rem !important; 
        line-height: 1.2 !important; 
        color: var(--c-neem) !important;
    }}
    h2:not(.cinematic-page-container *) {{ font-size: 1.55rem !important; margin-top: 1rem !important; color: var(--c-neem) !important; }}
    h3:not(.cinematic-page-container *) {{ font-size: 1.18rem !important; color: var(--c-neem) !important; }}

    p:not(.cinematic-page-container *), 
    span:not(.cinematic-page-container *):not([class*="material-symbols"]):not([data-testid="stIconMaterial"]):not([translate="no"]), 
    label:not(.cinematic-page-container *), 
    div:not(.cinematic-page-container *):not(.cinematic-page-container):not([class*="material-symbols"]):not([data-testid="stIconMaterial"]) {{
        font-family: var(--font-main);
        color: var(--c-ink);
    }}

    .stCaption, [data-testid="stCaptionContainer"] {{
        color: var(--c-muted) !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }}

    /* Modern Glassmorphic Container Cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: var(--c-card-glass) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.95) !important;
        border-radius: var(--radius-lg) !important;
        box-shadow: var(--shadow-glass) !important;
        padding: 1.2rem 1.4rem !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }}

    /* Modern Pill Buttons */
    .stButton > button {{
        font-family: var(--font-main) !important;
        border-radius: var(--radius-pill) !important;
        font-weight: 700 !important;
        padding: 0.65rem 1.6rem !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        border: 1px solid var(--c-border-accent) !important;
        background: #FFFFFF !important;
        color: var(--c-neem) !important;
        letter-spacing: 0.01em !important;
        box-shadow: 0 2px 8px rgba(22, 62, 43, 0.06) !important;
    }}

    .stButton > button:hover {{
        border-color: var(--c-neem) !important;
        background: var(--c-surface) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 18px rgba(22, 62, 43, 0.12) !important;
        color: var(--c-forest) !important;
    }}

    .stButton > button[kind="primary"], 
    .stButton > button[data-testid="baseButton-primary"] {{
        background: linear-gradient(135deg, #E5A010 0%, #D97706 50%, #B45309 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 6px 20px rgba(217, 119, 6, 0.35) !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
        padding: 0.75rem 2rem !important;
    }}

    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="baseButton-primary"]:hover {{
        background: linear-gradient(135deg, #F59E0B 0%, #E5A010 100%) !important;
        color: #FFFFFF !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 28px rgba(217, 119, 6, 0.45) !important;
    }}

    /* Form Inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox [data-baseweb="select"], .stTextArea textarea {{
        background-color: #FFFFFF !important;
        border: 1px solid rgba(22, 62, 43, 0.16) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--c-ink) !important;
        font-family: var(--font-main) !important;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.02) !important;
        font-weight: 600 !important;
    }}

    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {{
        border-color: var(--c-leaf) !important;
        box-shadow: 0 0 0 3px rgba(45, 106, 79, 0.16) !important;
    }}

    /* Metrics with Glass Aesthetics */
    div[data-testid="stMetric"] {{
        background: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(14px) !important;
        border: 1px solid rgba(255, 255, 255, 0.9) !important;
        border-radius: var(--radius-md) !important;
        padding: 16px 20px !important;
        box-shadow: var(--shadow-subtle) !important;
    }}

    div[data-testid="stMetricLabel"] p {{
        color: var(--c-muted) !important;
        font-size: 0.78rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
    }}

    div[data-testid="stMetricValue"] {{
        color: var(--c-neem) !important;
        font-weight: 800 !important;
        font-size: 1.85rem !important;
        font-family: var(--font-main) !important;
    }}

    /* =======================================================
       NAVIGATION BAR & MENU STYLING (BHARAT, REIMAGINED)
       ======================================================= */
    [data-testid="stSidebarContent"] {{
        display: flex !important;
        flex-direction: column !important;
        padding-top: 0.6rem !important;
        padding-bottom: 2rem !important;
    }}

    [data-testid="stSidebarUserContent"] {{
        padding: 0 !important;
        margin: 0 !important;
    }}

    [data-testid="stSidebarNav"] {{
        padding-top: 0.2rem !important;
        padding-bottom: 0.2rem !important;
    }}

    [data-testid="stSidebarNavItems"] {{
        gap: 3px !important;
    }}

    /* Section Header Titles for Category Groups */
    [data-testid="stSidebarNavSectionHeader"] {{
        display: block !important;
        visibility: visible !important;
        font-family: var(--font-main) !important;
        font-size: 0.72rem !important;
        font-weight: 800 !important;
        color: #526058 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        padding: 10px 8px 3px 8px !important;
        margin-top: 4px !important;
        margin-bottom: 2px !important;
        opacity: 1 !important;
        pointer-events: auto !important;
    }}

    [data-testid="stSidebarNavSectionHeader"] * {{
        font-family: var(--font-main) !important;
        font-size: 0.72rem !important;
        font-weight: 800 !important;
        color: #526058 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
    }}

    /* Navigation Links */
    [data-testid="stSidebarNavLink"] {{
        font-family: var(--font-main) !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: #163E2B !important;
        border-radius: 10px !important;
        padding: 8px 12px !important;
        margin: 2px 4px !important;
        transition: all 0.18s ease !important;
        border: 1px solid transparent !important;
        text-decoration: none !important;
    }}

    [data-testid="stSidebarNavLink"]:hover {{
        background: rgba(45, 106, 79, 0.08) !important;
        color: #163E2B !important;
        transform: translateX(3px) !important;
        border-color: rgba(45, 106, 79, 0.15) !important;
    }}

    /* Active / Current Page Navigation Link */
    [data-testid="stSidebarNavLink"][aria-current="page"] {{
        background: linear-gradient(135deg, rgba(217, 119, 6, 0.16) 0%, rgba(217, 119, 6, 0.08) 100%) !important;
        color: #163E2B !important;
        font-weight: 800 !important;
        border-left: 3px solid #D97706 !important;
        border-radius: 4px 10px 10px 4px !important;
        box-shadow: 0 2px 8px rgba(217, 119, 6, 0.08) !important;
    }}

    /* Nav Separators & View More Button */
    [data-testid="stSidebarNavSeparator"] {{
        border-bottom: 1px solid rgba(22, 62, 43, 0.1) !important;
        margin: 8px 0 !important;
    }}

    /* Hide Streamlit View More / View Less Navigation Toggle */
    [data-testid="stSidebarNavViewButton"] {{
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }}

    [data-testid="stSidebarNavItems"] {{
        max-height: none !important;
        overflow-y: visible !important;
    }}

    /* Custom Slim & Elegant Scrollbars (Fixes Scroller Issue) */
    ::-webkit-scrollbar {{
        width: 6px !important;
        height: 6px !important;
    }}
    ::-webkit-scrollbar-track {{
        background: transparent !important;
    }}
    ::-webkit-scrollbar-thumb {{
        background: rgba(22, 62, 43, 0.22) !important;
        border-radius: 4px !important;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: rgba(22, 62, 43, 0.42) !important;
    }}

    [data-testid="stSidebarContent"] {{
        scrollbar-width: thin !important;
        scrollbar-color: rgba(22, 62, 43, 0.22) transparent !important;
    }}

    section[data-testid="stSidebar"] .stButton > button {{
        white-space: nowrap !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
        padding: 6px 4px !important;
        min-height: 2.2rem !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        letter-spacing: -0.01em !important;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 12px !important;
        border-bottom: 2px solid var(--c-border) !important;
    }}

    .stTabs [data-baseweb="tab"] {{
        font-family: var(--font-main) !important;
        font-weight: 700 !important;
        color: var(--c-muted) !important;
        padding: 10px 18px !important;
    }}

    .stTabs [aria-selected="true"] {{
        color: var(--c-neem) !important;
        border-bottom: 3px solid var(--c-neem) !important;
        background-color: transparent !important;
    }}

    /* =======================================================
       CONTINUOUS HORIZONTAL ANIMATED TICKER (HIGH CONTRAST & READABLE)
       ======================================================= */

    @keyframes setuTickerMarquee {{
        0% {{ transform: translateX(0%); }}
        100% {{ transform: translateX(-50%); }}
    }}

    .setu-ticker-wrap {{
        display: flex;
        align-items: center;
        background: linear-gradient(90deg, #133826 0%, #1A4D34 50%, #133826 100%);
        border: 1px solid #1A4D34;
        border-radius: var(--radius-sm);
        padding: 8px 14px;
        margin-bottom: 1.3rem;
        box-shadow: 0 4px 18px rgba(19, 56, 38, 0.25);
        overflow: hidden;
        position: relative;
    }}

    .setu-ticker-badge-pill {{
        background: linear-gradient(135deg, #E5A010 0%, #D97706 100%);
        color: #FFFFFF !important;
        font-size: 0.74rem;
        font-weight: 900;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 5px 14px;
        border-radius: var(--radius-pill);
        display: inline-flex;
        align-items: center;
        gap: 7px;
        flex-shrink: 0;
        z-index: 3;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
    }}

    .pulse-live-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #FFFFFF;
        box-shadow: 0 0 8px #FFFFFF;
        display: inline-block;
        animation: blinkLive 1.4s ease-in-out infinite;
    }}

    @keyframes blinkLive {{
        0%, 100% {{ opacity: 1; transform: scale(1); }}
        50% {{ opacity: 0.3; transform: scale(0.7); }}
    }}

    .setu-ticker-viewport {{
        flex: 1;
        overflow: hidden;
        white-space: nowrap;
        position: relative;
        margin-left: 14px;
        mask-image: linear-gradient(to right, transparent, black 2%, black 98%, transparent);
        -webkit-mask-image: linear-gradient(to right, transparent, black 2%, black 98%, transparent);
    }}

    .setu-ticker-track {{
        display: inline-flex;
        align-items: center;
        white-space: nowrap;
        will-change: transform;
        animation: setuTickerMarquee 32s linear infinite;
    }}

    .setu-ticker-track:hover {{
        animation-play-state: paused;
    }}

    .setu-ticker-item {{
        display: inline-flex;
        align-items: center;
        gap: 9px;
        padding: 0 18px;
        font-size: 0.92rem;
        font-weight: 600;
        color: #FFFFFF !important;
    }}

    .setu-ticker-item b {{
        color: #FEEBC8 !important;
        font-weight: 800;
        letter-spacing: 0.04em;
    }}

    .setu-ticker-item span.crop-label {{
        color: #FFFFFF !important;
        font-weight: 600;
    }}

    .setu-ticker-item span.price-val {{
        color: #F7E9B7 !important;
        font-weight: 800;
    }}

    .ticker-up {{ 
        color: #22C55E !important; 
        font-weight: 900; 
        background: rgba(34, 197, 94, 0.22);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
    }}
    .ticker-down {{ 
        color: #EF4444 !important; 
        font-weight: 900; 
        background: rgba(239, 68, 68, 0.22);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
    }}
    .ticker-stable {{ 
        color: #FACC15 !important; 
        font-weight: 900; 
        background: rgba(250, 204, 21, 0.22);
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
    }}
    .ticker-sep {{ 
        color: #4E8C6D !important; 
        font-size: 0.85rem;
    }}

    /* =======================================================
       GLASSMORPHISM & AMBIENT MOTION GRADIENT CARDS
       ======================================================= */

    @keyframes ambientGradientGlow {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}

    .setu-glass-hero {{
        position: relative;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.85) 0%, rgba(248, 252, 249, 0.7) 100%);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border: 1px solid rgba(255, 255, 255, 0.95);
        border-radius: var(--radius-lg);
        padding: 36px 40px;
        margin-bottom: 2rem;
        box-shadow: var(--shadow-glass);
        overflow: hidden;
    }}

    .setu-glass-hero::before {{
        content: '';
        position: absolute;
        top: -40%;
        left: -20%;
        width: 140%;
        height: 180%;
        background: radial-gradient(circle at 20% 30%, rgba(45, 106, 79, 0.08) 0%, transparent 40%),
                    radial-gradient(circle at 80% 70%, rgba(217, 119, 6, 0.07) 0%, transparent 40%),
                    radial-gradient(circle at 50% 50%, rgba(30, 81, 40, 0.05) 0%, transparent 50%);
        background-size: 200% 200%;
        animation: ambientGradientGlow 15s ease infinite;
        pointer-events: none;
        z-index: 0;
    }}

    .setu-glass-content {{
        position: relative;
        z-index: 1;
    }}

    .setu-feature-row {{
        display: flex;
        align-items: flex-start;
        gap: 16px;
        padding: 16px;
        border-radius: var(--radius-md);
        background: rgba(255, 255, 255, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(10px);
        margin-bottom: 12px;
        transition: all 0.2s ease;
    }}

    .setu-feature-row:hover {{
        background: rgba(255, 255, 255, 0.95);
        transform: translateX(4px);
        box-shadow: 0 8px 24px rgba(22, 62, 43, 0.08);
        border-color: rgba(45, 106, 79, 0.3);
    }}

    .setu-feature-icon {{
        width: 44px;
        height: 44px;
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(22, 62, 43, 0.1) 0%, rgba(45, 106, 79, 0.18) 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
        flex-shrink: 0;
        color: var(--c-neem);
    }}

    .setu-feature-title {{
        font-size: 1.05rem;
        font-weight: 800;
        color: var(--c-neem);
        margin-bottom: 2px;
    }}

    .setu-feature-desc {{
        font-size: 0.86rem;
        color: var(--c-muted);
        line-height: 1.4;
    }}

    /* Floating Status Placeholder Card */
    .setu-floating-glass-card {{
        background: linear-gradient(145deg, rgba(255, 255, 255, 0.92) 0%, rgba(248, 252, 249, 0.82) 100%);
        border: 1px solid rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: var(--radius-lg);
        padding: 24px;
        box-shadow: var(--shadow-glass);
        position: relative;
    }}

    .setu-floating-flow-item {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 14px;
        border-radius: var(--radius-sm);
        background: rgba(255, 255, 255, 0.8);
        border: 1px solid rgba(22, 62, 43, 0.08);
        margin-bottom: 10px;
    }}

    .setu-flow-route {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.78rem;
        font-weight: 700;
        color: var(--c-muted);
    }}

    .setu-flow-line {{
        width: 32px;
        height: 2px;
        background: linear-gradient(90deg, var(--c-neem), var(--c-leaf));
        position: relative;
    }}
    .setu-flow-line::after {{
        content: '➔';
        position: absolute;
        right: -6px;
        top: -8px;
        font-size: 10px;
        color: var(--c-leaf);
    }}

    /* Pill Action Buttons */
    .setu-pill-btn-primary {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: linear-gradient(135deg, #E5A010 0%, #D97706 100%);
        color: #FFFFFF !important;
        font-weight: 800;
        font-size: 0.92rem;
        padding: 10px 24px;
        border-radius: var(--radius-pill);
        text-decoration: none !important;
        box-shadow: 0 4px 14px rgba(217, 119, 6, 0.3);
        transition: all 0.2s ease;
    }}

    .setu-pill-btn-primary:hover {{
        background: linear-gradient(135deg, #F59E0B 0%, #E5A010 100%);
        transform: translateY(-2px);
        box-shadow: 0 8px 22px rgba(217, 119, 6, 0.4);
        color: #FFFFFF !important;
    }}

    .setu-pill-btn-outline {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(255, 255, 255, 0.9);
        color: var(--c-neem) !important;
        font-weight: 700;
        font-size: 0.92rem;
        padding: 10px 24px;
        border-radius: var(--radius-pill);
        border: 1px solid var(--c-border-accent);
        text-decoration: none !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        transition: all 0.2s ease;
    }}

    .setu-pill-btn-outline:hover {{
        background: #FFFFFF;
        border-color: var(--c-neem);
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(22, 62, 43, 0.12);
        color: var(--c-forest) !important;
    }}

    /* =======================================================
       MODERN GLASS SIGN-IN CARD (IMAGE 3 CONCEPT)
       ======================================================= */

    .glass-auth-container {{
        position: relative;
        background: linear-gradient(180deg, rgba(255, 253, 248, 0.92) 0%, rgba(255, 255, 255, 0.85) 100%);
        backdrop-filter: blur(28px);
        -webkit-backdrop-filter: blur(28px);
        border: 1px solid rgba(255, 255, 255, 0.95);
        border-radius: 28px;
        padding: 38px 36px 32px 36px;
        box-shadow: 0 25px 60px -15px rgba(22, 62, 43, 0.1), 0 0 1px 1px rgba(255, 255, 255, 0.8);
        overflow: hidden;
        max-width: 480px;
        margin: 0 auto;
    }}

    .glass-auth-container::before {{
        content: '';
        position: absolute;
        top: -60px;
        left: 50%;
        transform: translateX(-50%);
        width: 220px;
        height: 120px;
        background: radial-gradient(ellipse, rgba(229, 160, 16, 0.25) 0%, transparent 70%);
        pointer-events: none;
        z-index: 0;
    }}

    .glass-auth-header {{
        text-align: center;
        position: relative;
        z-index: 1;
        margin-bottom: 22px;
    }}

    .glass-auth-logo {{
        max-height: 52px;
        margin-bottom: 12px;
        object-fit: contain;
    }}

    .glass-auth-title {{
        font-family: var(--font-main);
        font-size: 1.55rem;
        font-weight: 800;
        color: #163E2B;
        margin: 0 0 4px 0;
        letter-spacing: -0.02em;
    }}

    .glass-auth-subtitle {{
        font-size: 0.85rem;
        color: #526058;
        font-weight: 500;
    }}

    .glass-auth-divider {{
        display: flex;
        align-items: center;
        text-align: center;
        margin: 20px 0 16px 0;
        color: #8C9B92;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.08em;
    }}

    .glass-auth-divider::before, .glass-auth-divider::after {{
        content: '';
        flex: 1;
        border-bottom: 1px solid rgba(22, 62, 43, 0.12);
    }}
    .glass-auth-divider:not(:empty)::before {{
        margin-right: 12px;
    }}
    .glass-auth-divider:not(:empty)::after {{
        margin-left: 12px;
    }}

    .glass-pill-badge-row {{
        display: flex;
        justify-content: center;
        gap: 10px;
    }}

    .glass-pill-badge {{
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(22, 62, 43, 0.12);
        padding: 6px 14px;
        border-radius: var(--radius-pill);
        font-size: 0.76rem;
        font-weight: 700;
        color: #163E2B;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }}

    /* =======================================================
       ESC KEYBOARD SHORTCUT HUD & FLOATING CONTROLS
       ======================================================= */
    .esc-floating-pill {{
        position: fixed;
        bottom: 12px;
        right: 14px;
        z-index: 9999;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(22, 62, 43, 0.75);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid rgba(245, 158, 11, 0.35);
        color: #FFFFFF;
        padding: 4px 10px;
        border-radius: var(--radius-pill);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        font-size: 0.68rem;
        font-weight: 600;
        cursor: pointer;
        opacity: 0.35;
        transition: all 0.2s ease;
        user-select: none;
    }}

    .esc-floating-pill:hover {{
        opacity: 1.0;
        transform: translateY(-1px);
        background: #163E2B;
        border-color: #F59E0B;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.25);
    }}

    .esc-key-badge {{
        background: #F59E0B;
        color: #111813;
        font-weight: 900;
        font-size: 0.7rem;
        padding: 2px 7px;
        border-radius: 5px;
        letter-spacing: 0.04em;
    }}

    /* ESC HUD Modal Overlay */
    .esc-hud-overlay {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(10, 26, 17, 0.78);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        z-index: 999999;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: escFadeIn 0.15s ease-out forwards;
    }}

    @keyframes escFadeIn {{
        from {{ opacity: 0; transform: scale(0.96); }}
        to {{ opacity: 1; transform: scale(1); }}
    }}

    .esc-hud-card {{
        background: #FFFFFF;
        border: 1px solid rgba(22, 62, 43, 0.16);
        border-top: 4px solid #D97706;
        border-radius: 20px;
        padding: 24px 28px;
        width: 92%;
        max-width: 490px;
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.35);
        color: #111813;
        font-family: var(--font-main);
    }}

    .esc-hud-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }}

    .esc-hud-title {{
        font-size: 1.15rem;
        font-weight: 800;
        color: #163E2B;
        display: flex;
        align-items: center;
        gap: 8px;
    }}

    .esc-hud-close {{
        background: none;
        border: none;
        font-size: 1.25rem;
        cursor: pointer;
        color: #8C9B92;
        padding: 4px 8px;
        border-radius: 6px;
        transition: all 0.2s;
    }}

    .esc-hud-close:hover {{
        color: #163E2B;
        background: rgba(22, 62, 43, 0.08);
    }}

    .esc-hud-subtitle {{
        font-size: 0.82rem;
        color: #526058;
        margin-bottom: 18px;
    }}

    .esc-hud-actions {{
        display: flex;
        flex-direction: column;
        gap: 10px;
    }}

    .esc-action-btn {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 16px;
        border-radius: 12px;
        text-decoration: none !important;
        border: 1px solid rgba(22, 62, 43, 0.12);
        background: #F8F5EE;
        color: #111813 !important;
        transition: all 0.2s ease;
        cursor: pointer;
    }}

    .esc-action-btn:hover {{
        background: #FFFFFF;
        border-color: #D97706;
        transform: translateX(4px);
        box-shadow: 0 4px 14px rgba(217, 119, 6, 0.15);
    }}

    .esc-btn-left {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}

    .esc-btn-icon {{
        font-size: 1.35rem;
    }}

    .esc-btn-title {{
        font-size: 0.92rem;
        font-weight: 800;
        color: #163E2B;
    }}

    .esc-btn-sub {{
        font-size: 0.72rem;
        color: #526058;
    }}

    .esc-key-hint {{
        background: #FFFFFF;
        border: 1px solid rgba(22, 62, 43, 0.2);
        font-size: 0.7rem;
        font-weight: 800;
        color: #163E2B;
        padding: 3px 8px;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }}

    .esc-hud-footer {{
        margin-top: 16px;
        text-align: center;
        font-size: 0.72rem;
        color: #8C9B92;
        border-top: 1px solid rgba(22, 62, 43, 0.08);
        padding-top: 12px;
    }}

    /* =======================================================
       PREMIUM KISAN SETU FOOTER (TEAM HEXANODES · SIH 2026)
       ======================================================= */
    .setu-master-footer {{
        margin-top: 4rem;
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        width: 100%;
        position: relative;
        z-index: 5;
    }}

    .setu-footer-inner {{
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(22, 62, 43, 0.14);
        border-top: 3px solid #D97706;
        border-radius: 20px;
        padding: 22px 28px;
        box-shadow: 0 10px 30px rgba(22, 62, 43, 0.05);
    }}

    .setu-footer-top-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 14px;
    }}

    .setu-footer-brand-side {{
        display: flex;
        flex-direction: column;
        gap: 4px;
    }}

    .setu-footer-logo-badge {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }}

    .setu-footer-logo-text {{
        font-family: var(--font-brand);
        font-size: 1.15rem;
        font-weight: 900;
        color: #163E2B;
        letter-spacing: 0.03em;
    }}

    .setu-footer-slogan {{
        font-size: 0.8rem;
        color: #526058;
        font-weight: 500;
    }}

    .setu-footer-badges {{
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
    }}

    .setu-badge-sih {{
        background: linear-gradient(135deg, #163E2B 0%, #1F513A 100%);
        color: #F8F5EE;
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        padding: 6px 14px;
        border-radius: var(--radius-pill);
        box-shadow: 0 2px 8px rgba(22, 62, 43, 0.18);
        border: 1px solid rgba(245, 158, 11, 0.3);
    }}

    .setu-badge-ps {{
        background: rgba(217, 119, 6, 0.12);
        color: #B45309;
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        padding: 6px 14px;
        border-radius: var(--radius-pill);
        border: 1px solid rgba(217, 119, 6, 0.28);
    }}

    .setu-footer-divider {{
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(22, 62, 43, 0.12), transparent);
        margin: 16px 0 14px 0;
    }}

    .setu-footer-bottom-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    }}

    .setu-footer-credit {{
        font-size: 0.95rem;
        font-weight: 700;
        color: #163E2B;
        letter-spacing: -0.01em;
    }}

    .hexanodes-highlight {{
        color: #D97706;
        font-weight: 900;
        letter-spacing: 0.02em;
        background: linear-gradient(135deg, rgba(217, 119, 6, 0.14) 0%, rgba(245, 158, 11, 0.08) 100%);
        padding: 3px 10px;
        border-radius: 8px;
        border: 1px solid rgba(217, 119, 6, 0.25);
    }}

    .setu-footer-meta {{
        display: flex;
        align-items: center;
        gap: 14px;
        font-size: 0.74rem;
        color: #6D7D74;
        font-weight: 600;
        flex-wrap: wrap;
    }}

    /* Sidebar Footer Team Badge */
    .sidebar-team-badge {{
        margin-top: 20px;
        padding: 12px 14px;
        background: rgba(255, 255, 255, 0.85);
        border: 1px solid rgba(22, 62, 43, 0.12);
        border-left: 3px solid #D97706;
        border-radius: 12px;
        text-align: left;
    }}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


    # Injects ESC Shortcut HUD & Keyboard Listener on all pages
    esc_hud_html = """<div id="esc-hud-modal" class="esc-hud-overlay" style="display:none;" onclick="if(event.target===this) closeEscHud();">
<div class="esc-hud-card">
<div class="esc-hud-header">
<div class="esc-hud-title">
<span class="esc-key-badge">ESC</span>
Quick Return Navigator · सेतू नेव्हिगेटर
</div>
<button class="esc-hud-close" onclick="closeEscHud()">✕</button>
</div>
<div class="esc-hud-subtitle">Choose where you would like to navigate:</div>
<div class="esc-hud-actions">
<a href="#" onclick="handleEscNav('home', event)" class="esc-action-btn">
<div class="esc-btn-left">
<span class="esc-btn-icon">🏠</span>
<div>
<div class="esc-btn-title">Home Overview Dashboard</div>
<div class="esc-btn-sub">Ecosystem pulse, bridge telemetry & directives</div>
</div>
</div>
<span class="esc-key-hint">Press 1</span>
</a>
<a href="#" onclick="handleEscNav('component', event)" class="esc-action-btn">
<div class="esc-btn-left">
<span class="esc-btn-icon">🚀</span>
<div>
<div class="esc-btn-title">My Role Component Hub</div>
<div class="esc-btn-sub">Your primary workspace (AI Match / Procurement / Orders)</div>
</div>
</div>
<span class="esc-key-hint">Press 2</span>
</a>
<a href="#" onclick="handleEscNav('mandi', event)" class="esc-action-btn">
<div class="esc-btn-left">
<span class="esc-btn-icon">🏛️</span>
<div>
<div class="esc-btn-title">Digital Mandi Floor</div>
<div class="esc-btn-sub">Live trade ticker & regional arbitrage engine</div>
</div>
</div>
<span class="esc-key-hint">Press 3</span>
</a>
</div>
<div class="esc-hud-footer">
Tip: Press <span class="esc-key-badge" style="background:#E5DFD3; color:#163E2B;">ESC</span> anytime or click the badge below to toggle
</div>
</div>
</div>
<div class="esc-floating-pill" onclick="toggleEscHud()" title="Press ESC on your keyboard to navigate anywhere">
<span class="esc-key-badge">ESC</span>
<span>Quick Return</span>
</div>
<script>
    (function() {
        function getModal() {
            var targets = [document];
            try { if (window.parent && window.parent.document) targets.push(window.parent.document); } catch(e) {}
            try { if (window.top && window.top.document) targets.push(window.top.document); } catch(e) {}
            for (var i = 0; i < targets.length; i++) {
                if (targets[i]) {
                    var m = targets[i].getElementById('esc-hud-modal');
                    if (m) return m;
                }
            }
            return document.getElementById('esc-hud-modal');
        }

        function findAndClickNav(targetKey) {
            var targets = [document];
            try { if (window.parent && window.parent.document) targets.push(window.parent.document); } catch(e) {}
            try { if (window.top && window.top.document) targets.push(window.top.document); } catch(e) {}
            
            var links = [];
            for (var d = 0; d < targets.length; d++) {
                try {
                    var found = targets[d].querySelectorAll('a[data-testid="stSidebarNavLink"], section[data-testid="stSidebar"] a, [data-testid="stSidebarNav"] a');
                    if (found && found.length > 0) {
                        links = found;
                        break;
                    }
                } catch(e) {}
            }
            
            var clicked = false;
            for (var i = 0; i < links.length; i++) {
                var href = (links[i].getAttribute('href') || "").toLowerCase();
                var text = (links[i].innerText || "").toLowerCase();
                
                if (targetKey === 'home' && (href.indexOf('dashboard') !== -1 || href.indexOf('farmer-hub') !== -1 || text.indexOf('overview') !== -1 || text.indexOf('dashboard') !== -1)) {
                    links[i].click();
                    clicked = true;
                    break;
                } else if (targetKey === 'mandi' && (href.indexOf('digital-mandi') !== -1 || text.indexOf('digital mandi') !== -1 || text.indexOf('mandi') !== -1)) {
                    links[i].click();
                    clicked = true;
                    break;
                } else if (targetKey === 'component') {
                    if (href.indexOf('farmer') !== -1 || href.indexOf('ai-match') !== -1 ||
                        href.indexOf('buyer') !== -1 || href.indexOf('procurement') !== -1 ||
                        href.indexOf('consumer') !== -1 || href.indexOf('marketplace') !== -1 ||
                        href.indexOf('logistics') !== -1 || href.indexOf('dispatch') !== -1 ||
                        href.indexOf('admin') !== -1 || href.indexOf('market-intel') !== -1 ||
                        text.indexOf('match') !== -1 || text.indexOf('procurement') !== -1 ||
                        text.indexOf('marketplace') !== -1 || text.indexOf('dispatch') !== -1) {
                        links[i].click();
                        clicked = true;
                        break;
                    }
                }
            }
            
            if (!clicked) {
                if (targetKey === 'home') {
                    window.location.href = './dashboard';
                } else if (targetKey === 'mandi') {
                    window.location.href = './digital-mandi';
                }
            }
        }

        window.toggleEscHud = function() {
            var modal = getModal();
            if (!modal) return;
            if (modal.style.display === 'none' || modal.style.display === '') {
                modal.style.display = 'flex';
            } else {
                modal.style.display = 'none';
            }
        };

        window.closeEscHud = function() {
            var modal = getModal();
            if (modal) modal.style.display = 'none';
        };

        window.handleEscNav = function(targetKey, e) {
            if (e) e.preventDefault();
            closeEscHud();
            findAndClickNav(targetKey);
        };

        function onKeyDown(e) {
            if (e.key === 'Escape' || e.keyCode === 27) {
                e.preventDefault();
                e.stopPropagation();
                toggleEscHud();
            } else {
                var modal = getModal();
                if (modal && modal.style.display === 'flex') {
                    if (e.key === '1') { handleEscNav('home', e); }
                    else if (e.key === '2') { handleEscNav('component', e); }
                    else if (e.key === '3') { handleEscNav('mandi', e); }
                }
            }
        }

        var contexts = [window, document];
        try { if (window.parent && window.parent !== window) { contexts.push(window.parent, window.parent.document); } } catch(e) {}
        try { if (window.top && window.top !== window && window.top !== window.parent) { contexts.push(window.top, window.top.document); } } catch(e) {}

        contexts.forEach(function(ctx) {
            try {
                ctx.removeEventListener('keydown', onKeyDown, true);
                ctx.addEventListener('keydown', onKeyDown, true);
            } catch(e) {}
        });

        // Ensure sidebar is open and not accidentally collapsed
        function ensureSidebarOpen() {
            try {
                var doc = document;
                var expandBtn = doc.querySelector('[data-testid="stSidebarCollapsedControl"] button, [data-testid="collapsedControl"] button');
                var sidebar = doc.querySelector('section[data-testid="stSidebar"]');
                if (expandBtn && (!sidebar || sidebar.getAttribute('aria-expanded') === 'false' || window.getComputedStyle(sidebar).display === 'none')) {
                    expandBtn.click();
                }
            } catch(e) {}
        }
        setTimeout(ensureSidebarOpen, 50);
        setTimeout(ensureSidebarOpen, 300);

        // Seamless Vertical Sidebar Alignment (Places Top Header before Nav Tree)
        function alignSidebar() {
            try {
                var targets = [document];
                try { if (window.parent && window.parent.document) targets.push(window.parent.document); } catch(e) {}
                try { if (window.top && window.top.document) targets.push(window.top.document); } catch(e) {}
                
                for (var i = 0; i < targets.length; i++) {
                    var doc = targets[i];
                    var sidebar = doc.querySelector('section[data-testid="stSidebar"]') || doc.querySelector('[data-testid="stSidebar"]');
                    if (!sidebar) continue;
                    
                    var nav = sidebar.querySelector('[data-testid="stSidebarNav"]');
                    var topMarker = sidebar.querySelector('#kisan-setu-sidebar-top-marker');
                    if (nav && topMarker) {
                        var topBlock = topMarker.closest('[data-testid="stVerticalBlock"]') || topMarker.closest('[data-testid="stVerticalBlockBorderWrapper"]') || topMarker.parentElement;
                        if (topBlock && nav.parentElement) {
                            var containerParent = nav.parentElement;
                            if (topBlock.parentElement !== containerParent || topBlock.nextElementSibling !== nav) {
                                containerParent.insertBefore(topBlock, nav);
                            }
                        }
                    }
                }
            } catch(e) {}
        }
        alignSidebar();
        setInterval(alignSidebar, 120);
    })();
    </script>
    """
    st.markdown(esc_hud_html, unsafe_allow_html=True)


def render_sidebar_header():
    """Renders the official branding logo and subtitle once at the top of the sidebar."""
    logo_b64 = get_logo_base64()
    if logo_b64:
        sidebar_logo_html = f"""
        <div style="text-align: center; padding: 4px 4px 10px 4px; border-bottom: 1px solid rgba(22, 62, 43, 0.1); margin-bottom: 10px;">
            <img src="data:image/png;base64,{logo_b64}" style="max-width: 100%; height: auto; border-radius: 8px; max-height: 44px; object-fit: contain;" alt="Kisan Setu" />
            <div style="font-size: 0.7rem; font-weight: 800; color: #526058; letter-spacing: 0.08em; text-transform: uppercase; margin-top: 5px;">
                खेत से बाज़ार तक · 2026
            </div>
        </div>
        """
        st.markdown(sidebar_logo_html, unsafe_allow_html=True)
