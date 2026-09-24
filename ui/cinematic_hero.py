"""
Kisan Setu — Cinematic Video Landing Experience
'Bharat, Reimagined'
Full-bleed background video layer with layered earthy gradient vignette,
cinematic brand reveal, Setu connection animation, editorial live market snapshots,
and interactive role-driven authentication.
"""

import streamlit as st
import os
import base64
from datetime import datetime

from utils.data_loader import (
    load_prices,
    load_demand,
    load_produce,
)
from utils.auth import DEMO_USERS, login
from ui.theme import get_logo_base64


@st.cache_data(show_spinner=False)
def get_hero_video_base64():
    """
    Loads and caches the local Kisan Setu hero video as a base64 string.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    video_paths = [
        os.path.join(base_dir, "assets", "videos", "kisan_setu_hero.mp4"),
        os.path.join(base_dir, "assets", "videos", "3748157875-preview.mp4"),
        os.path.join(base_dir, "3748157875-preview.mp4"),
    ]
    for vp in video_paths:
        if os.path.exists(vp):
            try:
                with open(vp, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
            except Exception:
                continue
    return ""


def render_cinematic_landing():
    """
    Renders the full-screen cinematic video background landing page
    with storytelling progression:
    VIDEO -> BRAND REVEAL -> LIVE MARKET DETAIL -> SETU SIGNALS -> ENTER THE SETU -> SIGN IN
    """
    video_b64 = get_hero_video_base64()
    logo_b64 = get_logo_base64()

    # Load actual application market data snapshot
    prices_df = load_prices()
    demand_df = load_demand()

    # Today's formatted date
    date_display = datetime.now().strftime("%d %B %Y").upper()

    video_tag = ""
    if video_b64:
        video_tag = f"""
        <video class="cinematic-video-bg" autoplay loop muted playsinline preload="auto">
            <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
        </video>
        """

    logo_nav_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-height: 40px; width: auto; object-fit: contain;" alt="Kisan Setu" />' if logo_b64 else '<span style="font-size:1.6rem;">🌾</span>'

    # Master Cinematic Stylesheet
    st.markdown(
        f"""
        <style>
        /* =======================================================
           CINEMATIC FULL-SCREEN LAYERING ARCHITECTURE
           ======================================================= */

        /* Make entire Streamlit canvas transparent so video covers 100% */
        .stApp, 
        [data-testid="stAppViewContainer"], 
        [data-testid="stHeader"], 
        .main, 
        section.main {{
            background: transparent !important;
        }}

        /* Scope sidebar suppression to cinematic landing screen only */
        body:has(.cinematic-video-bg) [data-testid="stSidebar"],
        body:has(.cinematic-video-bg) [data-testid="collapsedControl"],
        body:has(.cinematic-video-bg) [data-testid="stSidebarCollapsedControl"],
        body:has(.cinematic-video-bg) section[data-testid="stSidebar"] {{
            display: none !important;
        }}

        .main .block-container {{
            background: transparent !important;
            padding-top: 1rem !important;
            max-width: 100% !important;
        }}

        /* Video Background Layer — Bright, Vivid, Full Bleed */
        .cinematic-video-bg {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            object-fit: cover;
            z-index: -3;
            pointer-events: none;
            filter: brightness(1.02) contrast(1.06) saturate(1.15);
            transform: scale(1.02);
        }}

        /* Translucent Earthy Multi-Stop Vignette & Gradient Overlay */
        .cinematic-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: -2;
            pointer-events: none;
            background: 
                radial-gradient(ellipse at 50% 35%, rgba(10, 28, 18, 0.28) 0%, rgba(6, 18, 12, 0.72) 100%),
                linear-gradient(180deg, rgba(8, 22, 14, 0.22) 0%, rgba(8, 20, 13, 0.65) 55%, rgba(5, 14, 9, 0.92) 100%);
        }}

        /* Subtle Film Texture */
        .cinematic-texture {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: -1;
            pointer-events: none;
            opacity: 0.025;
            background-image: radial-gradient(#FFFFFF 1px, transparent 1px);
            background-size: 4px 4px;
        }}

        /* Scrollable Content Container */
        .cinematic-page-container {{
            position: relative;
            z-index: 10;
            color: #FFFFFF !important;
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 1.5rem 5rem 1.5rem;
        }}

        .cinematic-page-container,
        .cinematic-page-container p,
        .cinematic-page-container span,
        .cinematic-page-container div,
        .cinematic-page-container h1,
        .cinematic-page-container h2,
        .cinematic-page-container h3,
        .cinematic-page-container a {{
            color: #FFFFFF;
        }}

        /* Floating Minimal Nav Bar */
        .cinematic-nav {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 22px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.15);
            margin-bottom: 2rem;
            animation: fadeInDown 1.2s ease forwards;
        }}

        .cinematic-nav-title {{
            font-family: 'Cinzel', Georgia, serif;
            font-size: 1.25rem;
            font-weight: 900;
            color: #FFFFFF !important;
            letter-spacing: 0.04em;
        }}

        .cinematic-nav-subtitle {{
            font-size: 0.72rem;
            color: #E5A010 !important;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        .cinematic-nav-links {{
            display: flex;
            align-items: center;
            gap: 22px;
        }}

        .cinematic-nav-link {{
            color: rgba(255, 255, 255, 0.9) !important;
            font-size: 0.82rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            text-decoration: none !important;
            transition: color 0.2s ease;
        }}

        .cinematic-nav-link:hover {{
            color: #E5A010 !important;
        }}

        .cinematic-nav-cta {{
            background: linear-gradient(135deg, #E5A010 0%, #D97706 100%) !important;
            color: #FFFFFF !important;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            padding: 8px 18px;
            border-radius: 9999px;
            text-decoration: none !important;
            box-shadow: 0 4px 14px rgba(217, 119, 6, 0.35);
        }}

        /* =======================================================
           SECTION 01: CINEMATIC HERO & BRAND REVEAL
           ======================================================= */

        .hero-title-section {{
            min-height: 75vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 40px 0 20px 0;
        }}

        .hero-eyebrow {{
            font-size: 0.84rem !important;
            font-weight: 800 !important;
            letter-spacing: 0.14em !important;
            text-transform: uppercase !important;
            color: #FFFFFF !important;
            margin-bottom: 18px !important;
            display: inline-flex !important;
            align-items: center !important;
            gap: 8px !important;
            text-shadow: 0 2px 8px rgba(0, 0, 0, 0.7) !important;
            animation: fadeInUp 1s ease forwards;
        }}

        .hero-eyebrow span {{
            color: #FFFFFF !important;
            font-size: 0.75rem !important;
        }}

        .hero-devanagari-headline {{
            font-family: 'Noto Sans Devanagari', 'Cinzel', serif !important;
            font-size: clamp(1.85rem, 3.8vw, 3.1rem) !important;
            font-weight: 900 !important;
            color: #FFFFFF !important;
            margin: 4px 0 10px 0 !important;
            line-height: 1.25 !important;
            letter-spacing: -0.01em !important;
            text-shadow: 0 4px 24px rgba(0, 0, 0, 0.7) !important;
            animation: fadeInUp 1.2s ease forwards;
        }}

        .hero-brand-name {{
            font-family: 'Cinzel', 'Playfair Display', Georgia, serif !important;
            font-size: clamp(3rem, 7vw, 5.6rem) !important;
            font-weight: 900 !important;
            letter-spacing: 0.04em !important;
            color: #FFFFFF !important;
            background: none !important;
            -webkit-background-clip: unset !important;
            -webkit-text-fill-color: #FFFFFF !important;
            margin: 0 0 14px 0 !important;
            line-height: 1 !important;
            text-shadow: 0 10px 30px rgba(0, 0, 0, 0.7) !important;
            animation: fadeInUp 1.4s ease forwards;
        }}

        .hero-subline {{
            font-size: clamp(1.05rem, 1.8vw, 1.35rem) !important;
            color: #FFFFFF !important;
            max-width: 680px !important;
            line-height: 1.55 !important;
            font-weight: 500 !important;
            margin-bottom: 32px !important;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.7) !important;
            animation: fadeInUp 1.6s ease forwards;
        }}

        .hero-scroll-hint {{
            font-size: 0.76rem !important;
            font-weight: 800 !important;
            letter-spacing: 0.12em !important;
            color: rgba(255, 255, 255, 0.85) !important;
            text-transform: uppercase !important;
            text-shadow: 0 2px 6px rgba(0, 0, 0, 0.6) !important;
        }}

        /* Setu Connection Line Animation */
        .setu-connection-visual {{
            display: inline-flex;
            align-items: center;
            gap: 16px;
            background: rgba(14, 38, 26, 0.65);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1.5px solid rgba(255, 255, 255, 0.22);
            border-radius: 9999px;
            padding: 10px 24px;
            margin-bottom: 40px;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
            animation: fadeInUp 1.8s ease forwards;
        }}

        .setu-connection-visual span {{
            color: #FFFFFF !important;
            font-weight: 800 !important;
            font-size: 0.85rem !important;
            letter-spacing: 0.06em !important;
        }}

        .setu-line-segment {{
            width: 60px;
            height: 2px;
            background: linear-gradient(90deg, transparent, #E5A010);
            position: relative;
        }}

        .setu-line-segment.right {{
            background: linear-gradient(90deg, #E5A010, transparent);
        }}

        .setu-central-node {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #E5A010;
            box-shadow: 0 0 16px #E5A010, 0 0 0 4px rgba(229, 160, 16, 0.25);
            animation: pulseGlow 2s ease-in-out infinite;
        }}

        @keyframes pulseGlow {{
            0%, 100% {{ transform: scale(1); box-shadow: 0 0 12px #E5A010, 0 0 0 3px rgba(229, 160, 16, 0.2); }}
            50% {{ transform: scale(1.25); box-shadow: 0 0 24px #E5A010, 0 0 0 6px rgba(229, 160, 16, 0.4); }}
        }}

        /* =======================================================
           SECTION 02: EDITORIAL LIVE MARKET DETAIL
           ======================================================= */

        .cinematic-section-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            border-bottom: 1px solid rgba(255, 255, 255, 0.15);
            padding-bottom: 14px;
            margin: 60px 0 26px 0;
        }}

        .cinematic-section-title {{
            font-family: 'Cinzel', 'Playfair Display', serif;
            font-size: 1.85rem;
            font-weight: 800;
            color: #FFFFFF;
            margin: 0;
            letter-spacing: 0.02em;
        }}

        .cinematic-section-meta {{
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            color: #E5A010;
            text-transform: uppercase;
        }}

        .market-editorial-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 18px;
            margin-bottom: 24px;
        }}

        .market-editorial-card {{
            background: rgba(16, 40, 28, 0.65);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-top: 3px solid #E5A010;
            border-radius: 16px;
            padding: 22px 20px;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}

        .market-editorial-card:hover {{
            transform: translateY(-4px);
            border-color: rgba(229, 160, 16, 0.45);
            background: rgba(18, 46, 32, 0.78);
        }}

        .market-card-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.72rem;
            font-weight: 800;
            color: #A0B4A8;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}

        .market-card-crop-en {{
            font-size: 1.45rem;
            font-weight: 800;
            color: #FFFFFF;
            line-height: 1.1;
        }}

        .market-card-crop-mr {{
            font-size: 0.95rem;
            font-weight: 600;
            color: #CBD5E1;
            margin-bottom: 12px;
        }}

        .market-card-price {{
            font-size: 2.1rem;
            font-weight: 800;
            color: #F7E9B7;
            letter-spacing: -0.02em;
            margin: 6px 0;
            display: flex;
            align-items: baseline;
            gap: 6px;
        }}

        .market-card-price span {{
            font-size: 0.9rem;
            font-weight: 600;
            color: #A0B4A8;
        }}

        .market-card-delta {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 0.8rem;
            font-weight: 800;
            padding: 3px 8px;
            border-radius: 6px;
        }}

        .delta-up {{
            color: #4ADE80;
            background: rgba(74, 222, 128, 0.16);
        }}
        .delta-down {{
            color: #F87171;
            background: rgba(248, 113, 113, 0.16);
        }}
        .delta-stable {{
            color: #FACC15;
            background: rgba(250, 204, 21, 0.16);
        }}

        /* Setu Signal Banner */
        .setu-signal-banner {{
            background: linear-gradient(135deg, rgba(22, 54, 38, 0.8) 0%, rgba(14, 36, 25, 0.85) 100%);
            backdrop-filter: blur(18px);
            border: 1px solid rgba(229, 160, 16, 0.3);
            border-left: 5px solid #E5A010;
            border-radius: 16px;
            padding: 18px 24px;
            margin: 20px 0 40px 0;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
        }}

        .signal-title {{
            font-size: 0.76rem;
            font-weight: 900;
            color: #E5A010;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 4px;
        }}

        .signal-text {{
            font-size: 1.05rem;
            font-weight: 700;
            color: #FFFFFF;
            line-height: 1.4;
        }}

        .signal-sub {{
            font-size: 0.82rem;
            color: #CBD5E1;
            margin-top: 4px;
        }}

        /* =======================================================
           SECTION 03: ENTER THE SETU & ROLE SELECTION CARDS
           ======================================================= */

        .role-selection-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin: 24px 0 36px 0;
        }}

        .role-glass-card {{
            background: rgba(18, 44, 31, 0.65);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 20px;
            padding: 24px 18px;
            text-align: center;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
            position: relative;
            cursor: pointer;
        }}

        .role-glass-card:hover {{
            transform: translateY(-6px);
            border-color: rgba(229, 160, 16, 0.6);
            background: rgba(22, 58, 40, 0.85);
            box-shadow: 0 14px 35px rgba(0, 0, 0, 0.35);
        }}

        .role-card-icon {{
            font-size: 2.2rem;
            margin-bottom: 8px;
            display: block;
        }}

        .role-card-title {{
            font-size: 1.15rem;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: 0.02em;
        }}

        .role-card-mr {{
            font-size: 0.85rem;
            font-weight: 600;
            color: #E5A010;
            margin: 2px 0 8px 0;
        }}

        .role-card-desc {{
            font-size: 0.78rem;
            color: #CBD5E1;
            line-height: 1.35;
        }}

        /* Keyframe Animations */
        @keyframes fadeInUp {{
            from {{ opacity: 0; transform: translateY(24px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        @keyframes fadeInDown {{
            from {{ opacity: 0; transform: translateY(-16px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* Auth Card Specific Styling */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: linear-gradient(145deg, rgba(16, 42, 30, 0.88) 0%, rgba(10, 28, 20, 0.92) 100%) !important;
            backdrop-filter: blur(28px) !important;
            -webkit-backdrop-filter: blur(28px) !important;
            border: 1.5px solid rgba(255, 255, 255, 0.22) !important;
            border-radius: 28px !important;
            padding: 34px 30px 26px 30px !important;
            box-shadow: 0 25px 60px -10px rgba(0, 0, 0, 0.65), 0 0 0 1px rgba(255, 255, 255, 0.15) !important;
            margin-bottom: 2rem !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] .glass-auth-header {{
            text-align: center !important;
            margin-bottom: 18px !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] .glass-auth-logo {{
            max-height: 48px !important;
            margin-bottom: 10px !important;
            object-fit: contain !important;
            display: inline-block !important;
            background: #FFFFFF !important;
            padding: 6px 14px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] .glass-auth-title,
        div[data-testid="stVerticalBlockBorderWrapper"] h2 {{
            font-family: var(--font-main) !important;
            font-size: 1.6rem !important;
            font-weight: 800 !important;
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            margin: 0 0 6px 0 !important;
            text-align: center !important;
            letter-spacing: -0.01em !important;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.7) !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] .glass-auth-subtitle {{
            font-size: 0.88rem !important;
            color: #E2E8F0 !important;
            -webkit-text-fill-color: #E2E8F0 !important;
            font-weight: 500 !important;
            text-align: center !important;
            margin-bottom: 20px !important;
            text-shadow: 0 1px 6px rgba(0, 0, 0, 0.7) !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] label,
        div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stWidgetLabel"] p {{
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            font-weight: 700 !important;
            font-size: 0.92rem !important;
            text-shadow: 0 1px 6px rgba(0, 0, 0, 0.8) !important;
            margin-bottom: 6px !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] [data-baseweb="select"] {{
            background-color: #FFFFFF !important;
            border: 1.5px solid rgba(255, 255, 255, 0.3) !important;
            border-radius: 12px !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] [data-baseweb="select"] span,
        div[data-testid="stVerticalBlockBorderWrapper"] [data-baseweb="select"] div {{
            color: #111813 !important;
            -webkit-text-fill-color: #111813 !important;
            font-weight: 600 !important;
            text-shadow: none !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button {{
            background: linear-gradient(135deg, #E5A010 0%, #D97706 50%, #B45309 100%) !important;
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            border: none !important;
            font-weight: 800 !important;
            font-size: 1.05rem !important;
            padding: 0.75rem 2rem !important;
            border-radius: 9999px !important;
            box-shadow: 0 6px 20px rgba(217, 119, 6, 0.5) !important;
            text-shadow: 0 1px 4px rgba(0, 0, 0, 0.4) !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button:hover {{
            background: linear-gradient(135deg, #F59E0B 0%, #E5A010 100%) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 10px 26px rgba(217, 119, 6, 0.6) !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] .glass-auth-divider {{
            display: flex;
            align-items: center;
            text-align: center;
            margin: 22px 0 18px 0;
            color: #F6C864 !important;
            -webkit-text-fill-color: #F6C864 !important;
            font-size: 0.74rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-shadow: 0 1px 8px rgba(0, 0, 0, 0.7) !important;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] .glass-auth-divider::before,
        div[data-testid="stVerticalBlockBorderWrapper"] .glass-auth-divider::after {{
            content: '';
            flex: 1;
            border-bottom: 1px solid rgba(255, 255, 255, 0.28);
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] .glass-auth-divider:not(:empty)::before {{
            margin-right: 12px;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] .glass-auth-divider:not(:empty)::after {{
            margin-left: 12px;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] .glass-pill-badge-row {{
            display: flex;
            justify-content: center;
            gap: 10px;
            flex-wrap: wrap;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] .glass-pill-badge {{
            background: rgba(255, 255, 255, 0.14) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(255, 255, 255, 0.25) !important;
            padding: 6px 14px !important;
            border-radius: 9999px !important;
            font-size: 0.76rem !important;
            font-weight: 700 !important;
            color: #FFFFFF !important;
            -webkit-text-fill-color: #FFFFFF !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important;
            text-shadow: 0 1px 4px rgba(0, 0, 0, 0.6) !important;
        }}

        /* Mobile Adjustments */
        @media (max-width: 768px) {{
            .hero-title-section {{ min-height: 60vh; padding: 20px 0; }}
            .market-editorial-grid {{ grid-template-columns: 1fr; }}
            .role-selection-grid {{ grid-template-columns: 1fr 1fr; }}
        }}
        </style>

        {video_tag}
        <div class="cinematic-overlay"></div>
        <div class="cinematic-texture"></div>
        """,
        unsafe_allow_html=True,
    )

    # HTML Story Flow Container
    landing_html = f"""<div class="cinematic-page-container">
<!-- TOP NAVIGATION -->
<nav class="cinematic-nav">
<div style="display: flex; align-items: center; gap: 12px;">
{logo_nav_html}
<div>
<div style="font-family: 'Cinzel', Georgia, serif; font-size: 1.25rem; font-weight: 900; color: #FFFFFF !important; letter-spacing: 0.04em;">KISAN SETU</div>
<div style="font-size: 0.72rem; color: #E5A010 !important; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;">किसान से बाज़ार तक · 2026</div>
</div>
</div>
<div class="cinematic-nav-links">
<a href="#market-section" class="cinematic-nav-link" style="color: #FFFFFF !important; text-shadow: 0 1px 4px rgba(0,0,0,0.6);">TODAY'S MARKET</a>
<a href="#enter-section" class="cinematic-nav-link" style="color: #FFFFFF !important; text-shadow: 0 1px 4px rgba(0,0,0,0.6);">ROLES</a>
<a href="#auth-section" class="cinematic-nav-cta" style="color: #FFFFFF !important;">ENTER THE SETU ➔</a>
</div>
</nav>

<!-- SECTION 01: HERO BRAND REVEAL -->
<section class="hero-title-section">
<div class="hero-eyebrow" style="color: #FFFFFF !important; font-size: 0.84rem; font-weight: 800; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 18px; display: inline-flex; align-items: center; gap: 8px; text-shadow: 0 2px 8px rgba(0, 0, 0, 0.7);">
<span style="color: #FFFFFF !important;">●</span> <span style="color: #FFFFFF !important;">{date_display} · MAHARASHTRA CORRIDOR</span>
</div>
<div class="hero-devanagari-headline" style="color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; font-family: 'Noto Sans Devanagari', 'Cinzel', serif !important; font-size: clamp(1.85rem, 3.8vw, 3.1rem) !important; font-weight: 900 !important; line-height: 1.25 !important; letter-spacing: -0.01em !important; text-shadow: 0 4px 24px rgba(0, 0, 0, 0.8) !important; margin: 4px 0 10px 0 !important;">
खेत से बाज़ार तक.
</div>
<h1 class="hero-brand-name" style="color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; font-family: 'Cinzel', 'Playfair Display', Georgia, serif !important; font-size: clamp(3rem, 7vw, 5.6rem) !important; font-weight: 900 !important; letter-spacing: 0.04em !important; background: none !important; line-height: 1 !important; text-shadow: 0 10px 30px rgba(0, 0, 0, 0.8) !important; margin: 0 0 14px 0 !important;">
KISAN SETU
</h1>
<div class="hero-subline" style="color: #FFFFFF !important; -webkit-text-fill-color: #FFFFFF !important; font-size: clamp(1.05rem, 1.8vw, 1.35rem) !important; max-width: 680px !important; line-height: 1.55 !important; font-weight: 500 !important; margin-bottom: 32px !important; text-shadow: 0 2px 10px rgba(0, 0, 0, 0.8) !important;">
India's intelligent farm-to-market network connecting farmers directly with institutional buyers, verified crop provenance, and route-optimized logistics.
</div>

<div class="setu-connection-visual" style="display: inline-flex; align-items: center; gap: 16px; background: rgba(14, 38, 26, 0.7); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1.5px solid rgba(255, 255, 255, 0.22); border-radius: 9999px; padding: 10px 24px; margin-bottom: 40px; box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);">
<span style="font-weight: 800; font-size: 0.85rem; color: #FFFFFF !important; letter-spacing: 0.06em;">🌾 FARM</span>
<span class="setu-line-segment"></span>
<span class="setu-central-node"></span>
<span class="setu-line-segment right"></span>
<span style="font-weight: 800; font-size: 0.85rem; color: #FFFFFF !important; letter-spacing: 0.06em;">🛒 MARKET</span>
</div>

<div class="hero-scroll-hint" style="font-size: 0.76rem !important; font-weight: 800 !important; letter-spacing: 0.12em !important; color: rgba(255, 255, 255, 0.85) !important; text-transform: uppercase !important; text-shadow: 0 2px 6px rgba(0, 0, 0, 0.7) !important;">
SCROLL TO EXPLORE MARKET SNAPSHOT ↓
</div>
</section>

<!-- SECTION 02: LIVE MARKET DETAIL -->
<section id="market-section" style="padding: 30px 0;">
<div class="cinematic-section-header">
<div>
<div class="cinematic-section-meta">LIVE MANDI TELEMETRY · थेट बाजारपेठ</div>
<h2 class="cinematic-section-title">Today's Market Floor</h2>
</div>
<div style="font-size: 0.82rem; color: #A0B4A8; font-weight: 600;">
Active Corridor: <b>Nashik ➔ Pune ➔ Mumbai</b>
</div>
</div>

<div class="market-editorial-grid">
<div class="market-editorial-card">
<div class="market-card-top">
<span>📍 NASHIK MANDI</span>
<span class="market-card-delta delta-up">↑ 6.2%</span>
</div>
<div class="market-card-crop-en">ONION</div>
<div class="market-card-crop-mr">कांदा · Grade A</div>
<div class="market-card-price">₹28.40 <span>/ kg</span></div>
<div style="font-size: 0.78rem; color: #A0B4A8; margin-top: 6px;">Demand: <b style="color: #4ADE80;">HIGH VELOCITY</b></div>
</div>

<div class="market-editorial-card">
<div class="market-card-top">
<span>📍 PUNE WHOLESALE</span>
<span class="market-card-delta delta-up">↑ 4.1%</span>
</div>
<div class="market-card-crop-en">TOMATO</div>
<div class="market-card-crop-mr">टोमॅटो · Hybrid Fresh</div>
<div class="market-card-price">₹34.20 <span>/ kg</span></div>
<div style="font-size: 0.78rem; color: #A0B4A8; margin-top: 6px;">Demand: <b style="color: #4ADE80;">STEADY INFLOW</b></div>
</div>

<div class="market-editorial-card">
<div class="market-card-top">
<span>📍 MUMBAI VASHI</span>
<span class="market-card-delta delta-down">↓ 2.8%</span>
</div>
<div class="market-card-crop-en">POTATO</div>
<div class="market-card-crop-mr">बटाटा · Local Lot</div>
<div class="market-card-price">₹26.80 <span>/ kg</span></div>
<div style="font-size: 0.78rem; color: #A0B4A8; margin-top: 6px;">Demand: <b style="color: #FACC15;">MODERATE</b></div>
</div>

<div class="market-editorial-card">
<div class="market-card-top">
<span>📍 AHMEDNAGAR</span>
<span class="market-card-delta delta-stable">→ STABLE</span>
</div>
<div class="market-card-crop-en">WHEAT</div>
<div class="market-card-crop-mr">गहू · Sharbati Grade A</div>
<div class="market-card-price">₹31.50 <span>/ kg</span></div>
<div style="font-size: 0.78rem; color: #A0B4A8; margin-top: 6px;">Demand: <b style="color: #4ADE80;">SUSTAINED</b></div>
</div>
</div>

<div class="setu-signal-banner">
<div class="signal-title">✦ SETU INTELLIGENCE SIGNAL</div>
<div class="signal-text">
Onion demand is strengthening across the Pune-Mumbai retail corridor (+₹2.60/kg arbitrage spread vs local arrivals).
</div>
<div class="signal-sub">
Algorithmically derived from live wholesale mandi arrivals, NH60 transport capacity, and institutional procurement requisitions.
</div>
</div>
</section>

<!-- SECTION 03: ENTER THE SETU -->
<section id="enter-section" style="padding: 20px 0 10px 0;">
<div class="cinematic-section-header">
<div>
<div class="cinematic-section-meta">ECOSYSTEM PARTICIPATION · सेतू प्रवेश</div>
<h2 class="cinematic-section-title">Enter The Setu</h2>
</div>
<div style="font-size: 0.82rem; color: #E5A010; font-weight: 700;">
SELECT YOUR ROLE
</div>
</div>

<div class="role-selection-grid">
<div class="role-glass-card">
<span class="role-card-icon">🌾</span>
<div class="role-card-title">FARMER</div>
<div class="role-card-mr">तुमची शेती</div>
<div class="role-card-desc">Sell harvest lots & discover fair realization without middlemen.</div>
</div>

<div class="role-glass-card">
<span class="role-card-icon">🛒</span>
<div class="role-card-title">BUYER</div>
<div class="role-card-mr">खरेदीदार</div>
<div class="role-card-desc">Source verified farm lots direct from growers with farm passports.</div>
</div>

<div class="role-glass-card">
<span class="role-card-icon">🛍️</span>
<div class="role-card-title">CONSUMER</div>
<div class="role-card-mr">ग्राहक</div>
<div class="role-card-desc">Fresh farm-to-table produce with 100% origin traceability.</div>
</div>

<div class="role-glass-card">
<span class="role-card-icon">🚚</span>
<div class="role-card-title">LOGISTICS</div>
<div class="role-card-mr">वाहतूक</div>
<div class="role-card-desc">Consolidated multi-farm transport via Setu Load routes.</div>
</div>

<div class="role-glass-card">
<span class="role-card-icon">🏛️</span>
<div class="role-card-title">ADMIN</div>
<div class="role-card-mr">प्रशासक</div>
<div class="role-card-desc">Statewide agricultural observatory & price monitoring.</div>
</div>
</div>
</section>
</div>"""
    st.markdown(landing_html, unsafe_allow_html=True)

    # SECTION 04: STREAMLIT AUTHENTICATION SECTION (ANCHORED)
    st.markdown("<div id='auth-section' style='padding-top: 10px;'></div>", unsafe_allow_html=True)
    left, center, right = st.columns([1, 1.8, 1])

    with center:
        with st.container(border=True):
            # Centered Auth Header
            logo_img_html = f'<img src="data:image/png;base64,{logo_b64}" class="glass-auth-logo" alt="Kisan Setu" />' if logo_b64 else '<div style="font-size:2.4rem; margin-bottom:8px;">🌾</div>'
            st.markdown(
                f"""<div class="glass-auth-header">
{logo_img_html}
<h2 class="glass-auth-title" style="color:#FFFFFF !important; text-shadow: 0 2px 10px rgba(0,0,0,0.7);">Sign In to Kisan Setu</h2>
<div class="glass-auth-subtitle" style="color:#E2E8F0 !important; text-shadow: 0 1px 6px rgba(0,0,0,0.7);">Select your ecosystem role and demo profile to continue</div>
</div>""",
                unsafe_allow_html=True,
            )

            role_choice = st.selectbox(
                "Ecosystem Role / तुमची भूमिका",
                [
                    "👨‍🌾 Farmer / FPO (शेतकरी)",
                    "🛒 Buyer / Retailer (खरेदीदार)",
                    "🛍️ Consumer (ग्राहक)",
                    "🚚 Logistics Provider (वाहतूकदार)",
                    "🏛️ Government / Admin (प्रशासक)",
                ],
            )

            role_map = {
                "👨‍🌾 Farmer / FPO (शेतकरी)": "Farmer",
                "🛒 Buyer / Retailer (खरेदीदार)": "Buyer",
                "🛍️ Consumer (ग्राहक)": "Consumer",
                "🚚 Logistics Provider (वाहतूकदार)": "Logistics",
                "🏛️ Government / Admin (प्रशासक)": "Admin",
            }

            selected_role = role_map[role_choice]

            available_users = [
                uid
                for uid, u in DEMO_USERS.items()
                if u["role"] == selected_role
            ]

            user_labels = {
                uid: f"{DEMO_USERS[uid]['icon']} {DEMO_USERS[uid]['name']} ({uid})"
                for uid in available_users
            }

            selected_user_id = st.selectbox(
                "Select Verified Profile / प्रोफाइल निवडा",
                available_users,
                format_func=lambda x: user_labels.get(x, x),
            )

            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

            if st.button(
                "ENTER THE SETU ➔",
                type="primary",
                use_container_width=True,
            ):
                if login(selected_user_id):
                    st.rerun()

            st.markdown(
                """<div class="glass-auth-divider">AUTHENTICATED DIGITAL CORRIDOR</div>
<div class="glass-pill-badge-row">
<span class="glass-pill-badge">🌾 Farmer Network</span>
<span class="glass-pill-badge">🛒 Wholesale Terminal</span>
<span class="glass-pill-badge">🚚 Setu Logistics</span>
</div>""",
                unsafe_allow_html=True,
            )

