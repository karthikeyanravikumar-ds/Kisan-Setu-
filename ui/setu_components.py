"""
Kisan Setu Signature Components
'Bharat, Reimagined'
Editorial Information Hierarchy, Live Horizontal Marquee Ticker, Glassmorphic Feature Placeholders & Farm Passports
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from ui.theme import get_logo_base64

# ------------------------------------------------------------
# HTML RENDERING UTILITY (Bypasses markdown code block pitfalls)
# ------------------------------------------------------------

def render_html(html_str: str):
    """
    Safely renders raw HTML in Streamlit.
    Prefers st.html() to avoid markdown parsers converting indented HTML
    or blank lines into code blocks (<pre><code>). Falls back to st.markdown.
    """
    if hasattr(st, "html"):
        st.html(html_str)
    else:
        st.markdown(html_str, unsafe_allow_html=True)



# ============================================================
# 0. BRAND HEADER (LOGO + EDITORIAL TITLE ACROSS ALL DASHBOARDS)
# ============================================================

def render_brand_header(title="KISAN SETU", subtitle="India's Intelligent Farm-to-Market Network", badge="BHARAT REIMAGINED · 2026"):
    """
    Renders the official Kisan Setu brand header with the exact logo image,
    Devanagari serif typography, and status indicators across all dashboard pages.
    """
    logo_b64 = get_logo_base64()
    logo_img_html = f'<img src="data:image/png;base64,{logo_b64}" style="max-height: 48px; width: auto; object-fit: contain;" alt="Kisan Setu" />' if logo_b64 else '<span style="font-size:1.8rem;">🌾</span>'

    html = f"""
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px; background: rgba(255, 255, 255, 0.75); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.9); border-radius: 16px; padding: 14px 22px; margin-bottom: 1.4rem; box-shadow: 0 4px 20px rgba(22, 62, 43, 0.05);">
        <div style="display: flex; align-items: center; gap: 16px;">
            {logo_img_html}
            <div>
                <div style="font-family: 'Cinzel', 'Playfair Display', Georgia, serif; font-size: 1.28rem; font-weight: 800; color: #163E2B; letter-spacing: 0.02em; line-height: 1.1;">
                    {title}
                </div>
                <div style="font-size: 0.82rem; color: #526058; font-weight: 500; margin-top: 2px;">
                    {subtitle}
                </div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="display: inline-flex; align-items: center; gap: 6px; background: linear-gradient(135deg, rgba(22, 62, 43, 0.08) 0%, rgba(45, 106, 79, 0.14) 100%); color: #163E2B; border: 1px solid rgba(22, 62, 43, 0.18); padding: 5px 14px; border-radius: 9999px; font-size: 0.74rem; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase;">
                <span style="width: 6px; height: 6px; border-radius: 50%; background: #2D6A4F; display: inline-block;"></span>
                {badge}
            </div>
        </div>
    </div>
    """
    render_html(html)


# ============================================================
# 1. BHARAT MARKET PULSE (Continuous Horizontal Live Moving Ticker)
# ============================================================

def render_bharat_market_pulse(items=None):
    """
    Renders a continuous horizontal moving marquee ticker across India's key mandis.
    Dynamically fetches live daily prices from data.gov.in API #1 (Current Daily Price).
    """
    if items is None:
        try:
            from data_ingestion.market_data import get_live_mandi_pulse_items
            items = get_live_mandi_pulse_items()
        except Exception:
            items = []

    if not items:
        items = [
            {"market": "NASHIK", "crop": "कांदा (Onion)", "price": "₹38.00", "change": "+5.2%", "status": "up"},
            {"market": "PUNE", "crop": "टोमॅटो (Tomato)", "price": "₹18.00", "change": "STABLE", "status": "stable"},
            {"market": "MUMBAI", "crop": "बटाटा (Potato)", "price": "₹26.00", "change": "-1.5%", "status": "down"},
            {"market": "AHILYANAGAR", "crop": "गहू (Wheat)", "price": "₹31.50", "change": "STABLE", "status": "stable"},
        ]

    def build_item_html(it):
        status_cls = f"ticker-{it['status']}"
        icon = "↑" if it['status'] == 'up' else ("↓" if it['status'] == 'down' else "→")
        return (
            f'<div class="setu-ticker-item">'
            f'<b>{it["market"]}</b> {it["crop"]}: <span>{it["price"]}</span> '
            f'<span class="{status_cls}">{icon} {it["change"]}</span>'
            f'</div>'
        )

    # Render twice for infinite seamless loop animation
    track_html = ' <span class="ticker-sep">✦</span> '.join([build_item_html(it) for it in items])
    seamless_loop_html = f'{track_html} <span class="ticker-sep">✦</span> {track_html}'

    ticker_html = f"""
    <div class="setu-ticker-wrap">
        <div class="setu-ticker-badge-pill">
            <span class="pulse-live-dot"></span> LIVE MANDI PULSE
        </div>
        <div class="setu-ticker-viewport">
            <div class="setu-ticker-track">
                {seamless_loop_html}
            </div>
        </div>
    </div>
    """
    render_html(ticker_html)


def render_mandi_status_badge():
    """
    Renders a subtle, clean live status indicator displaying API connectivity and provenance.
    """
    try:
        from data_ingestion.market_data import get_mandi_data_status
        status = get_mandi_data_status()
    except Exception:
        status = {
            "is_live": False,
            "status_badge": "● FALLBACK",
            "last_updated": datetime.now().strftime("%d %b %Y, %I:%M %p"),
            "source": "Local Dataset",
            "color": "#B45309",
        }

    badge_color = status.get("color", "#176536")
    badge_text = status.get("status_badge", "● LIVE — data.gov.in")
    updated_str = status.get("last_updated", "")
    source_str = status.get("source", "data.gov.in / AGMARKNET")

    html = f"""
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; background: rgba(255, 255, 255, 0.92); border: 1px solid rgba(22, 62, 43, 0.12); border-radius: 8px; padding: 6px 14px; margin-bottom: 12px; font-size: 0.8rem; color: #526058;">
        <div><strong style="color: {badge_color};">{badge_text}</strong> · Updated: {updated_str}</div>
        <div style="font-size: 0.75rem; color: #68756C;">Source: <b>{source_str}</b></div>
    </div>
    """
    render_html(html)


# ============================================================
# 2. GLASSMORPHIC HERO WITH AMBIENT MOTION GRADIENT (IMAGE 3 REFERENCE)
# ============================================================

def render_glass_feature_hero():
    """
    Renders the modern fintech-inspired glass placeholder with ambient motion gradient,
    structured features list, pill buttons, and interactive route preview (inspired by Image 3).
    """
    html = """<div class="setu-glass-hero">
<div class="setu-glass-content">
<div style="display: grid; grid-template-columns: 1.2fr 0.95fr; gap: 32px; align-items: center;">
<div>
<div style="font-family: 'Cinzel', 'Playfair Display', Georgia, serif; font-size: 1.85rem; font-weight: 800; color: #163E2B; line-height: 1.2; margin-bottom: 8px;">
Seamless Agricultural Liquidity
</div>
<p style="font-size: 0.95rem; color: #526058; margin-bottom: 22px; line-height: 1.5;">
Direct farm-to-mandi algorithmic matching with real-time price discovery, verified provenance, and aggregated dispatch corridors.
</p>
<div class="setu-feature-row">
<div class="setu-feature-icon">✦</div>
<div>
<div class="setu-feature-title">Algorithmic Match Engine</div>
<div class="setu-feature-desc">Instant trade discovery between verified farmer lots and institutional buyers.</div>
</div>
</div>
<div class="setu-feature-row">
<div class="setu-feature-icon">⚡</div>
<div>
<div class="setu-feature-title">One-Tap Mandi Dispatch</div>
<div class="setu-feature-desc">Lock competitive mandi bids and trigger route-optimized pickup in under 60 seconds.</div>
</div>
</div>
<div class="setu-feature-row">
<div class="setu-feature-icon">🛡️</div>
<div>
<div class="setu-feature-title">Immutable Farm Passport</div>
<div class="setu-feature-desc">Every quintal backed by digital soil grade verification and full harvest traceability.</div>
</div>
</div>
<div style="display: flex; gap: 14px; margin-top: 24px; flex-wrap: wrap;">
<a href="#explore" class="setu-pill-btn-primary">Explore Mandi Floor ➔</a>
<a href="#passport" class="setu-pill-btn-outline">View Provenance ↗</a>
</div>
</div>
<div class="setu-floating-glass-card">
<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; border-bottom: 1px solid rgba(22, 62, 43, 0.08); padding-bottom: 12px;">
<div>
<div style="font-size: 0.72rem; font-weight: 800; color: #526058; text-transform: uppercase; letter-spacing: 0.06em;">ACTIVE SETU LOT</div>
<div style="font-size: 1.45rem; font-weight: 800; color: #163E2B; font-family: var(--font-main);">₹28,400 <span style="font-size: 0.85rem; color: #2D6A4F; font-weight: 700;">(10 Qtl)</span></div>
</div>
<div style="background: linear-gradient(135deg, #163E2B, #235D3A); color: #FFFFFF; font-size: 0.72rem; font-weight: 800; padding: 4px 10px; border-radius: 9999px;">
LIVE LOT #KS-9482
</div>
</div>
<div style="background: rgba(22, 62, 43, 0.04); border: 1px dashed rgba(22, 62, 43, 0.16); border-radius: 10px; padding: 10px 14px; margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center;">
<div style="font-size: 0.75rem; color: #526058; font-weight: 600;">Farmer ID · शेतकरी</div>
<div style="font-size: 0.82rem; font-weight: 800; color: #163E2B; font-family: monospace;">KS·MH·NSK·0417</div>
</div>
<div class="setu-floating-flow-item">
<div style="display: flex; align-items: center; gap: 10px;">
<div style="width: 32px; height: 32px; border-radius: 8px; background: rgba(45, 106, 79, 0.12); display: flex; align-items: center; justify-content: center; font-size: 1rem;">🌾</div>
<div>
<div style="font-size: 0.85rem; font-weight: 800; color: #163E2B;">Nashik Farm (Patil)</div>
<div class="setu-flow-route">
<span>Sent</span> <span class="setu-flow-line"></span> <span>Pune Mandi</span>
</div>
</div>
</div>
<div style="text-align: right;">
<div style="font-size: 0.95rem; font-weight: 800; color: #163E2B;">₹14,200</div>
<div style="font-size: 0.7rem; color: #2D6A4F; font-weight: 700;">In Transit</div>
</div>
</div>
<div class="setu-floating-flow-item">
<div style="display: flex; align-items: center; gap: 10px;">
<div style="width: 32px; height: 32px; border-radius: 8px; background: rgba(217, 119, 6, 0.12); display: flex; align-items: center; justify-content: center; font-size: 1rem;">🏬</div>
<div>
<div style="font-size: 0.85rem; font-weight: 800; color: #163E2B;">FreshMart Retail (Buyer)</div>
<div class="setu-flow-route">
<span>Escrow Secured</span>
</div>
</div>
</div>
<div style="text-align: right;">
<div style="font-size: 0.95rem; font-weight: 800; color: #163E2B;">₹14,200</div>
<div style="font-size: 0.7rem; color: #D97706; font-weight: 700;">94% Match</div>
</div>
</div>
<div style="margin-top: 14px; padding-top: 10px; border-top: 1px solid rgba(22, 62, 43, 0.08); display: flex; justify-content: space-between; align-items: center; font-size: 0.78rem; color: #526058;">
<span>✦ Direct Settlement via UPI/Escrow</span>
<span style="font-weight: 800; color: #2D6A4F;">✓ Zero Middleman Fee</span>
</div>
</div>
</div>
</div>
</div>"""
    render_html(html)


def render_glass_auth_header():
    """
    Renders the modern mobile/glass-card sign-in header (inspired by Image 3).
    """
    logo_b64 = get_logo_base64()
    logo_img_html = f'<img src="data:image/png;base64,{logo_b64}" class="glass-auth-logo" alt="Kisan Setu" />' if logo_b64 else '<div style="font-size:2.4rem; margin-bottom:8px;">🌾</div>'

    html = f"""<div class="glass-auth-header">
{logo_img_html}
<h2 class="glass-auth-title">Welcome Back to Kisan Setu</h2>
<div class="glass-auth-subtitle">Select your ecosystem role and demo profile to continue</div>
</div>"""
    render_html(html)


# ============================================================
# 3. SETU PULSE (Node-Connected Ecosystem Bar)
# ============================================================

def render_setu_pulse(farmers_count=1248, avg_price=28.40, buyers_count=347, fulfilment_rate=94):
    """
    Renders the living status line for the agricultural network with connecting nodes.
    FARMERS ●───────────● MARKET ●───────────● BUYERS ●───────────● LOGISTICS
    """
    html = f"""<div class="setu-pulse-node-bar" style="background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.95); border-radius: 16px; padding: 16px 24px; margin-bottom: 1.5rem; box-shadow: 0 4px 20px rgba(22, 62, 43, 0.05);">
<div class="pulse-nodes-flow" style="display: flex; align-items: center; justify-content: space-between; position: relative;">
<div class="pulse-connecting-line" style="position: absolute; top: 8px; left: 30px; right: 30px; height: 2px; background: linear-gradient(90deg, #163E2B 0%, #D97706 50%, #163E2B 100%); z-index: 1;"></div>
<div class="pulse-node-item" style="display: flex; flex-direction: column; align-items: center; text-align: center; z-index: 2; background: rgba(255,255,255,0.95); padding: 0 12px; border-radius: 8px;">
<div class="pulse-node-dot" style="width: 14px; height: 14px; border-radius: 50%; background: #163E2B; border: 3px solid #FFFDF9; box-shadow: 0 0 0 2px #163E2B; margin-bottom: 6px;"></div>
<div class="pulse-node-label" style="font-size: 0.72rem; font-weight: 800; text-transform: uppercase; color: #526058; letter-spacing: 0.06em;">FARMERS · शेतकरी</div>
<div class="pulse-node-val" style="font-size: 1.25rem; font-weight: 800; color: #163E2B; margin-top: 2px;">{farmers_count:,}</div>
<div class="pulse-node-sub" style="font-size: 0.72rem; color: #526058;">Active Lots</div>
</div>
<div class="pulse-node-item" style="display: flex; flex-direction: column; align-items: center; text-align: center; z-index: 2; background: rgba(255,255,255,0.95); padding: 0 12px; border-radius: 8px;">
<div class="pulse-node-dot" style="width: 14px; height: 14px; border-radius: 50%; background: #D97706; border: 3px solid #FFFDF9; box-shadow: 0 0 0 2px #D97706; margin-bottom: 6px;"></div>
<div class="pulse-node-label" style="font-size: 0.72rem; font-weight: 800; text-transform: uppercase; color: #526058; letter-spacing: 0.06em;">MANDI MODAL · आजचा भाव</div>
<div class="pulse-node-val" style="font-size: 1.25rem; font-weight: 800; color: #163E2B; margin-top: 2px;">₹{avg_price:.2f}/kg</div>
<div class="pulse-node-sub" style="font-size: 0.72rem; color: #2D6A4F; font-weight: 700;">↑ 6.2% Spread</div>
</div>
<div class="pulse-node-item" style="display: flex; flex-direction: column; align-items: center; text-align: center; z-index: 2; background: rgba(255,255,255,0.95); padding: 0 12px; border-radius: 8px;">
<div class="pulse-node-dot" style="width: 14px; height: 14px; border-radius: 50%; background: #163E2B; border: 3px solid #FFFDF9; box-shadow: 0 0 0 2px #163E2B; margin-bottom: 6px;"></div>
<div class="pulse-node-label" style="font-size: 0.72rem; font-weight: 800; text-transform: uppercase; color: #526058; letter-spacing: 0.06em;">BUYERS · खरेदीदार</div>
<div class="pulse-node-val" style="font-size: 1.25rem; font-weight: 800; color: #163E2B; margin-top: 2px;">{buyers_count:,}</div>
<div class="pulse-node-sub" style="font-size: 0.72rem; color: #526058;">Retail & Wholesale</div>
</div>
<div class="pulse-node-item" style="display: flex; flex-direction: column; align-items: center; text-align: center; z-index: 2; background: rgba(255,255,255,0.95); padding: 0 12px; border-radius: 8px;">
<div class="pulse-node-dot" style="width: 14px; height: 14px; border-radius: 50%; background: #2D6A4F; border: 3px solid #FFFDF9; box-shadow: 0 0 0 2px #2D6A4F; margin-bottom: 6px;"></div>
<div class="pulse-node-label" style="font-size: 0.72rem; font-weight: 800; text-transform: uppercase; color: #526058; letter-spacing: 0.06em;">LOGISTICS · सेतू वाहतूक</div>
<div class="pulse-node-val" style="font-size: 1.25rem; font-weight: 800; color: #163E2B; margin-top: 2px;">{fulfilment_rate}%</div>
<div class="pulse-node-sub" style="font-size: 0.72rem; color: #2D6A4F; font-weight: 700;">Route Optimized</div>
</div>
</div>
</div>"""
    render_html(html)


# ============================================================
# 4. SETU BRIDGE INTERACTION FLOW
# ============================================================

def render_setu_bridge(left_label="FARM / शेत", left_sub="Nashik Rural",
                       center_label="SETU INTELLIGENCE · 94% MATCH",
                       right_label="MARKET / बाज़ार", right_sub="Pune Wholesale Hub"):
    """
    Visualizes the functional bridge connection between farm and market.
    """
    html = f"""
    <div style="background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(14px); border: 1px solid rgba(22, 62, 43, 0.12); border-radius: 16px; padding: 18px 24px; margin: 1.2rem 0; box-shadow: 0 4px 16px rgba(22, 62, 43, 0.04);">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
            <div style="flex: 1; min-width: 160px;">
                <div style="font-size: 0.7rem; font-weight: 800; color: #526058; text-transform: uppercase; letter-spacing: 0.06em;">ORIGIN / मूळ</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #163E2B;">🌾 {left_label}</div>
                <div style="font-size: 0.8rem; color: #526058;">{left_sub}</div>
            </div>
            <div style="display: flex; align-items: center; gap: 8px; background: linear-gradient(135deg, #163E2B 0%, #235D3A 100%); color: #FFFFFF; padding: 6px 16px; border-radius: 9999px; font-size: 0.76rem; font-weight: 800; letter-spacing: 0.05em;">
                <span>✦ {center_label} ✦</span>
            </div>
            <div style="flex: 1; min-width: 160px; text-align: right;">
                <div style="font-size: 0.7rem; font-weight: 800; color: #526058; text-transform: uppercase; letter-spacing: 0.06em;">DESTINATION / गंतव्य</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #163E2B;">🛒 {right_label}</div>
                <div style="font-size: 0.8rem; color: #526058;">{right_sub}</div>
            </div>
        </div>
    </div>
    """
    render_html(html)


# ============================================================
# 5. EDITORIAL MORNING BRIEFING HERO
# ============================================================

def render_morning_briefing(
    farmer_name="Ramesh",
    main_produce="ONION · कांदा",
    price_str="₹28.40 / KG",
    change_str="↑ 6.2% Today",
    mandi_name="Nashik Mandi · Grade A",
    available_kg=500,
    buyers_count=3,
    match_score=94,
    recommendation_text="Wait 48 hours before selling. Demand in Pune wholesale corridor is projected to rise 11–14%.",
    benchmarks=None
):
    """
    Signature Editorial Morning Briefing:
    Converts agricultural analytics into an intelligent companion experience.
    """
    if benchmarks is None:
        benchmarks = [
            {"market": "Nashik", "price": "₹28.4", "delta": "↑ 6.2%", "color": "#2D6A4F"},
            {"market": "Pune", "price": "₹31.2", "delta": "↑ 8.8%", "color": "#2D6A4F"},
            {"market": "Mumbai", "price": "₹33.1", "delta": "↑ 5.4%", "color": "#2D6A4F"},
            {"market": "Ahmednagar", "price": "₹27.8", "delta": "↓ 1.2%", "color": "#B45309"},
        ]

    date_str = datetime.now().strftime("%d %B %Y").upper()

    chips_html = "".join([
        f'<div style="background: rgba(255,255,255,0.85); border: 1px solid rgba(22,62,43,0.12); border-radius: 8px; padding: 8px 12px; text-align: center; min-width: 90px; display: inline-block;">'
        f'<div style="font-size: 0.72rem; font-weight: 800; color: #526058; text-transform: uppercase;">{b["market"]}</div>'
        f'<div style="font-size: 1.1rem; font-weight: 800; color: #163E2B; margin: 2px 0;">{b["price"]}</div>'
        f'<div style="font-size: 0.72rem; font-weight: 700; color: {b["color"]};">{b["delta"]}</div>'
        f'</div>'
        for b in benchmarks
    ])

    html = f"""<div style="background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(20px); border: 1px solid rgba(255, 255, 255, 0.95); border-radius: 20px; padding: 26px 30px; margin-bottom: 1.6rem; box-shadow: 0 10px 30px rgba(22, 62, 43, 0.06);">
<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(22, 62, 43, 0.1); padding-bottom: 10px; margin-bottom: 16px; font-size: 0.78rem; font-weight: 800; color: #526058; letter-spacing: 0.08em; text-transform: uppercase;">
<span>KISAN SETU · कृषी सेतू</span>
<span>{date_str}</span>
</div>
<div style="font-family: 'Cinzel', 'Playfair Display', Georgia, serif; font-size: 2.1rem; font-weight: 800; color: #163E2B; letter-spacing: -0.02em; line-height: 1.1;">
नमस्कार, {farmer_name}.
</div>
<div style="font-size: 1.05rem; color: #526058; margin: 6px 0 20px 0; font-weight: 500;">
Your farm is in prime condition today · तुमची शेती आज उत्तम स्थितीत आहे.
</div>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; background: rgba(248, 252, 249, 0.75); border: 1px solid rgba(22, 62, 43, 0.1); border-radius: 12px; padding: 16px 20px; margin-bottom: 18px;">
<div style="border-right: 1px dashed rgba(22, 62, 43, 0.14); padding-right: 12px;">
<div style="font-size: 0.72rem; font-weight: 800; color: #526058; text-transform: uppercase;">TODAY'S BENCHMARK · आजचा भाव</div>
<div style="font-size: 1.65rem; font-weight: 800; color: #163E2B; margin: 2px 0;">{price_str} <span style="font-size: 0.9rem; color: #2D6A4F;">{change_str}</span></div>
<div style="font-size: 0.78rem; color: #526058;">{main_produce} · {mandi_name}</div>
</div>
<div style="border-right: 1px dashed rgba(22, 62, 43, 0.14); padding-right: 12px;">
<div style="font-size: 0.72rem; font-weight: 800; color: #526058; text-transform: uppercase;">THIS WEEK IN YOUR FARM</div>
<div style="font-size: 1.65rem; font-weight: 800; color: #163E2B; margin: 2px 0;">{available_kg:,} KG</div>
<div style="font-size: 0.78rem; color: #526058;">Available Harvest · Grade A</div>
</div>
<div>
<div style="font-size: 0.72rem; font-weight: 800; color: #526058; text-transform: uppercase;">AI BUYER MATCH · जुळवणी</div>
<div style="font-size: 1.65rem; font-weight: 800; color: #163E2B; margin: 2px 0;">{match_score}% MATCH</div>
<div style="font-size: 0.78rem; color: #2D6A4F; font-weight: 700;">{buyers_count} Institutional Bidders Active</div>
</div>
</div>
<div style="background: rgba(255, 255, 255, 0.9); border: 1px solid rgba(22, 62, 43, 0.12); border-left: 4px solid #D97706; border-radius: 8px; padding: 14px 18px; margin-bottom: 16px;">
<div style="font-size: 0.72rem; font-weight: 800; color: #D97706; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 4px;">✦ SETU SUGGESTS · आजचा सेतू सल्ला</div>
<div style="font-size: 0.98rem; font-weight: 700; color: #163E2B;">"{recommendation_text}"</div>
<div style="font-size: 0.8rem; color: #526058; margin-top: 4px;">Confidence: <b>94%</b> · Based on wholesale arrivals, NH60 freight capacity, and Pune retail velocity.</div>
</div>
<div style="display: flex; gap: 10px; flex-wrap: wrap;">
{chips_html}
</div>
</div>"""
    render_html(html)


# ============================================================
# 6. MANDI PRICE CHIT COMPONENT
# ============================================================

def render_price_chit(crop_en, crop_mr, price, market, time_str="TODAY · 11:30 AM", change_str="+6.2%", is_up=True):
    """
    Renders a modernized Mandi Price Chit inspired by traditional Indian auction slips.
    """
    change_color = "#2D6A4F" if is_up else "#B45309"
    change_icon = "↑" if is_up else "↓"

    html = f"""
    <div style="background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(22, 62, 43, 0.12); border-top: 4px solid #163E2B; border-radius: 12px; padding: 16px 18px; box-shadow: 0 4px 14px rgba(22, 62, 43, 0.04); transition: transform 0.15s ease;">
        <div style="display: flex; justify-content: space-between; font-size: 0.7rem; font-weight: 800; color: #B45309; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 6px;">
            <span>आजचा भाव · MANDI CHIT</span>
            <span>📍 {market}</span>
        </div>
        <div style="font-size: 1.25rem; font-weight: 800; color: #163E2B; line-height: 1.1;">{crop_en}</div>
        <div style="font-size: 0.92rem; font-weight: 600; color: #526058; margin-bottom: 8px;">{crop_mr}</div>
        <div style="font-size: 1.75rem; font-weight: 800; color: #111813; letter-spacing: -0.02em; margin: 6px 0;">₹{price:.2f} <span style="font-size: 0.88rem; font-weight: 600; color: #526058;">/ KG</span></div>
        <div style="border-top: 1px dashed rgba(22, 62, 43, 0.12); margin-top: 10px; padding-top: 8px; display: flex; justify-content: space-between; align-items: center; font-size: 0.78rem; color: #526058;">
            <span>🕒 {time_str}</span>
            <span style="color: {change_color}; font-weight: 800;">{change_icon} {change_str}</span>
        </div>
    </div>
    """
    render_html(html)


# ============================================================
# 7. SETU SCORE BENCHMARK (0-100)
# ============================================================

def render_setu_score(score=88, label="Setu Trade Score", factors=None):
    """
    Renders the agricultural opportunity score (0-100) with rating factors.
    """
    if factors is None:
        factors = ["Price Spread: +₹2.60/kg", "Demand Velocity: High", "Route Efficiency: 94%"]

    factor_pills = "".join([f'<span style="background: rgba(255,255,255,0.8); border: 1px solid rgba(22,62,43,0.12); padding: 3px 10px; border-radius: 9999px; font-size: 0.74rem; color: #526058; margin-right: 6px; font-weight: 600;">{f}</span>' for f in factors])

    html = f"""
    <div style="background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(14px); border: 1px solid rgba(22, 62, 43, 0.12); border-radius: 14px; padding: 14px 20px; display: flex; align-items: center; justify-content: space-between; margin: 10px 0; box-shadow: 0 4px 16px rgba(22, 62, 43, 0.04);">
        <div style="display: flex; align-items: center; gap: 14px;">
            <div style="width: 48px; height: 48px; border-radius: 50%; background: linear-gradient(135deg, #163E2B 0%, #235D3A 100%); color: #D97706; font-weight: 800; font-size: 1.25rem; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(22, 62, 43, 0.25);">
                {score}
            </div>
            <div>
                <div style="font-size: 0.92rem; font-weight: 800; color: #163E2B;">{label} (संधी निर्देशांक)</div>
                <div style="margin-top: 4px;">{factor_pills}</div>
            </div>
        </div>
        <div style="text-align: right;">
            <span style="font-size: 0.75rem; font-weight: 800; color: #2D6A4F; background: rgba(45, 106, 79, 0.1); border: 1px solid rgba(45, 106, 79, 0.2); padding: 5px 12px; border-radius: 9999px;">
                HIGH VIABILITY · उच्च संभाव्यता
            </span>
        </div>
    </div>
    """
    render_html(html)


# ============================================================
# 8. FARM PASSPORT (Digital Provenance Identity)
# ============================================================

def render_farm_passport(farmer_name, location, crop, harvest_date, grade, match_score=94, logistics_route="Route #4"):
    """
    Renders the immutable digital provenance passport for produce lots.
    """
    html = f"""
    <div style="background: rgba(255, 255, 255, 0.88); backdrop-filter: blur(16px); border: 1px solid rgba(22, 62, 43, 0.14); border-radius: 14px; padding: 14px 18px; margin: 10px 0; box-shadow: 0 4px 16px rgba(22, 62, 43, 0.04);">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(22, 62, 43, 0.08); padding-bottom: 6px; margin-bottom: 8px;">
            <div style="font-size: 0.74rem; font-weight: 800; color: #163E2B; text-transform: uppercase; letter-spacing: 0.06em;">🌾 FARM PASSPORT · शेती प्रमाणपत्र</div>
            <div style="font-family: monospace; font-size: 0.72rem; color: #526058; font-weight: 700;">ID: KS-{abs(hash(farmer_name + crop)) % 1000000:06d}</div>
        </div>
        <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 8px; font-size: 0.82rem; color: #111813;">
            <span>शेतकरी:</span> <b>{farmer_name}</b> ({location})
            <span style="color:#526058;">·</span>
            <span>पीक:</span> <b>{crop}</b> (Grade {grade})
            <span style="color:#526058;">·</span>
            <span>कापणी:</span> <b>{harvest_date}</b>
            <span style="color:#526058;">·</span>
            <span>Setu Match:</span> <b style="color: #2D6A4F;">{match_score}%</b>
            <span style="color:#526058;">·</span>
            <span>वाहतूक:</span> <b>{logistics_route}</b>
            <span style="color:#526058;">·</span>
            <span style="background: rgba(45, 106, 79, 0.12); color: #2D6A4F; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 800;">✓ VERIFIED BHARAT LOT</span>
        </div>
    </div>
    """
    render_html(html)


# ============================================================
# 9. MARKET OPPORTUNITY LAYER
# ============================================================

def render_market_opportunity_layer(destination="Pune Market", destination_price=31.00, local_mandi="Nashik", local_price=28.40, confidence=87, extra_income=1300):
    """
    Quantifies exact financial upside across regional trade corridors.
    """
    delta = destination_price - local_price
    html = f"""
    <div style="background: rgba(255, 255, 255, 0.88); backdrop-filter: blur(16px); border: 1px solid rgba(22, 62, 43, 0.12); border-top: 4px solid #B45309; border-radius: 14px; padding: 18px 22px; margin: 14px 0; box-shadow: 0 4px 18px rgba(22, 62, 43, 0.05);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div>
                <div style="font-size: 0.72rem; font-weight: 800; color: #B45309; letter-spacing: 0.08em; text-transform: uppercase;">
                    संधी · BEST MARKET OPPORTUNITY
                </div>
                <div style="font-size: 1.35rem; font-weight: 800; color: #163E2B; margin: 4px 0;">
                    {destination} offers ₹{destination_price:.2f}/kg
                </div>
                <div style="font-size: 0.86rem; color: #526058;">
                    +₹{delta:.2f}/kg vs {local_mandi} (₹{local_price:.2f}/kg) · {confidence}% Demand Confidence
                </div>
            </div>
            <div style="text-align: right; background: rgba(248, 252, 249, 0.8); border: 1px dashed rgba(22, 62, 43, 0.18); border-radius: 10px; padding: 10px 18px;">
                <div style="font-size: 0.7rem; color: #526058; text-transform: uppercase; font-weight: 700;">ADDITIONAL REALIZATION</div>
                <div style="font-size: 1.45rem; font-weight: 800; color: #2D6A4F;">+₹{extra_income:,}</div>
            </div>
        </div>
    </div>
    """
    render_html(html)


# ============================================================
# 10. WHAT SHOULD I DO TODAY? ACTION CARDS
# ============================================================

def render_what_should_i_do(actions=None):
    """
    Action cards converting analytics into immediate actions:
    SELL · WAIT · MOVE · LIST · CONSOLIDATE
    """
    if actions is None:
        actions = [
            {"type": "sell", "label": "SELL · विक्री करा", "title": "Pune Wholesale Opportunity", "desc": "Current demand at Pune Fresh Retail allows ₹31/kg (+₹2.60/kg premium)."},
            {"type": "wait", "label": "WAIT · थांबा", "title": "Grade A Onion Surge", "desc": "Nashik arrivals slowing; local prices projected to gain 8–11% in 48h."},
            {"type": "move", "label": "MOVE · हलवा", "title": "Ahmednagar Mandi Spread", "desc": "Tomato deficit in Ahmednagar creates a ₹4.50/kg margin window."},
            {"type": "consolidate", "label": "CONSOLIDATE · एकत्र करा", "title": "Shared Logistics Available", "desc": "2 neighboring farms dispatching to Pune tomorrow; share vehicle to save ₹840."},
        ]

    cards_html = []
    for act in actions:
        cards_html.append(f"""
        <div style="background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(22, 62, 43, 0.12); border-radius: 12px; padding: 16px; transition: transform 0.15s ease;">
            <div style="display: inline-block; background: #163E2B; color: #FFFFFF; font-size: 0.7rem; font-weight: 800; padding: 3px 10px; border-radius: 9999px; text-transform: uppercase; margin-bottom: 8px;">{act['label']}</div>
            <div style="font-size: 0.95rem; font-weight: 800; color: #163E2B; margin-bottom: 4px;">{act['title']}</div>
            <div style="font-size: 0.82rem; color: #526058; line-height: 1.4;">{act['desc']}</div>
        </div>
        """)

    html = f"""
    <div style="margin: 1.2rem 0;">
        <div style="font-size: 0.78rem; font-weight: 800; color: #526058; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 10px;">
            ✦ आज काय करावे? · WHAT SHOULD I DO TODAY?
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px;">
            {''.join(cards_html)}
        </div>
    </div>
    """
    render_html(html)


# ============================================================
# 11. SETU LOAD (Smart Route Consolidation)
# ============================================================

def render_setu_load(farmers_count=3, buyers_count=2, route_name="Niphad → Sangamner → Pune", savings_amount=840, score=94):
    """
    Visualizes multiple farmers sharing a single logistics line.
    """
    html = f"""
    <div style="background: rgba(255, 255, 255, 0.88); backdrop-filter: blur(14px); border: 1px solid rgba(22, 62, 43, 0.12); border-radius: 14px; padding: 18px 22px; margin: 14px 0; box-shadow: 0 4px 16px rgba(22, 62, 43, 0.04);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; margin-bottom: 12px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="background: #163E2B; color: #D97706; font-size: 0.75rem; font-weight: 800; padding: 4px 12px; border-radius: 9999px;">SETU LOAD</span>
                <span style="font-size: 0.98rem; font-weight: 800; color: #163E2B;">Smart Logistics Consolidation</span>
            </div>
            <span style="font-size: 0.8rem; font-weight: 700; color: #2D6A4F; background: rgba(45, 106, 79, 0.12); padding: 4px 12px; border-radius: 9999px;">
                Setu Route Score: {score}/100
            </span>
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; background: rgba(248, 252, 249, 0.8); border: 1px dashed rgba(22, 62, 43, 0.16); border-radius: 10px; padding: 12px 18px;">
            <div style="font-size: 0.88rem; color: #111813;">
                <b>{farmers_count} Farmers</b> (Niphad + Rahata) ➔ <b>{buyers_count} Buyers</b> via <b>{route_name}</b>
            </div>
            <div style="font-size: 1.15rem; font-weight: 800; color: #2D6A4F;">
                ₹{savings_amount:,} Saved (-38% Transport Cost)
            </div>
        </div>
    </div>
    """
    render_html(html)


# ============================================================
# 12. FARM-TO-TABLE STORYTELLING
# ============================================================

def render_farm_to_table_story(steps=None):
    """
    Renders provenance storytelling for consumers and buyers.
    """
    if steps is None:
        steps = [
            {"title": "Nashik Valley Orchard (Niphad)", "meta": "Farmer Ramesh Patil · Soil-tested Grade A harvest"},
            {"title": "Harvested Dawn · 06 Sep", "meta": "Hand-picked and sorted at source"},
            {"title": "AI Quality Verified · Grade A", "meta": "Checked for size uniformity and skin texture"},
            {"title": "Packed & Dispatched · 07 Sep", "meta": "Moisture-safe crates via Setu Consolidated Route #4"},
            {"title": "Delivered Fresh To Your Table", "meta": "Zero middleman touchpoints · Direct realization"},
        ]

    steps_html = []
    for s in steps:
        steps_html.append(f"""
        <div style="padding: 10px 14px; background: rgba(255, 255, 255, 0.7); border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #2D6A4F;">
            <div style="font-size: 0.9rem; font-weight: 800; color: #163E2B;">{s['title']}</div>
            <div style="font-size: 0.78rem; color: #526058; margin-top: 2px;">{s['meta']}</div>
        </div>
        """)

    html = f"""
    <div style="background: rgba(255, 255, 255, 0.88); backdrop-filter: blur(16px); border: 1px solid rgba(22, 62, 43, 0.12); border-radius: 14px; padding: 20px; margin: 14px 0;">
        <div style="font-size: 0.8rem; font-weight: 800; color: #526058; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px;">
            🌱 FROM FARM TO TABLE · शेतापासून ताटापर्यंत
        </div>
        <div class="story-timeline">
            {''.join(steps_html)}
        </div>
    </div>
    """
    render_html(html)


# ============================================================
# 13. AI ACTIVITY VISUALIZATION SEQUENCE
# ============================================================

def render_ai_activity_sequence(steps_done=6, match_score=94):
    """
    Visualizes progressive intelligent AI matching rather than a generic spinner.
    """
    steps = [
        "Checking crop & variety compatibility",
        "Comparing batch quantity with buyer lot requirement",
        "Analysing live mandi benchmark prices & spreads",
        "Evaluating road distance & fuel realization",
        "Checking destination buyer demand velocity",
        "Calculating composite Setu Match Score",
    ]

    items_html = []
    for i, s in enumerate(steps):
        is_done = i < steps_done
        icon = '<span style="color:#2D6A4F; font-weight:800; margin-right:6px;">✓</span>' if is_done else '<span style="color:#A0AEC0; margin-right:6px;">○</span>'
        items_html.append(f'<div style="font-size:0.82rem; color:#163E2B; padding:3px 0;">{icon} <span>{s}</span></div>')

    html = f"""
    <div style="background: rgba(255, 255, 255, 0.9); border: 1px solid rgba(22, 62, 43, 0.14); border-radius: 12px; padding: 14px 18px; margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid rgba(22, 62, 43, 0.1); padding-bottom: 6px;">
            <span style="font-size: 0.78rem; font-weight: 800; color: #163E2B; text-transform: uppercase;">✦ SETU AI MATCHING SEQUENCE</span>
            <span style="font-size: 0.8rem; font-weight: 800; color: #2D6A4F;">{match_score}% MATCH FOUND</span>
        </div>
        {''.join(items_html)}
    </div>
    """
    render_html(html)


# ============================================================
# 14. AGRICULTURAL WEATHER INTELLIGENCE (Farm Pulse)
# ============================================================

def render_weather_intelligence(chain_items=None, insight_text="Localized rain in Nashik may disrupt tomato transit; prices expected to firm up in Pune."):
    """
    Turns weather data into actionable business insight chains.
    """
    if chain_items is None:
        chain_items = [
            ("RAIN IN NASHIK", "हवामान इशारा"),
            ("TRANSPORT RISK ↑", "वाहतूक जोखीम"),
            ("SUPPLY ARRIVALS ↓", "आवक घट"),
            ("PRICE PROJECTED ↑", "भाव वाढ अपेक्षित"),
        ]

    chain_html = []
    for title, sub in chain_items:
        chain_html.append(f"""
        <div style="text-align: center; padding: 8px 14px; background: rgba(255, 255, 255, 0.85); border: 1px solid rgba(22, 62, 43, 0.12); border-radius: 8px;">
            <div style="font-size: 0.82rem; font-weight: 800; color: #163E2B;">{title}</div>
            <div style="font-size: 0.7rem; color: #526058;">{sub}</div>
        </div>
        """)

    html = f"""
    <div style="background: rgba(255, 253, 249, 0.9); border: 1px solid rgba(22, 62, 43, 0.14); border-radius: 14px; padding: 16px 20px; margin: 14px 0;">
        <div style="font-size: 0.74rem; font-weight: 800; color: #B45309; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px;">
            🌦️ FARM PULSE · WEATHER & MARKET TRANSMISSION
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin: 10px 0;">
            {' <span style="color:#B45309; font-weight:800;">➔</span> '.join(chain_html)}
        </div>
        <div style="font-size: 0.84rem; color: #111813; margin-top: 10px; font-weight: 500;">
            <b>Market Implication:</b> {insight_text}
        </div>
    </div>
    """
    render_html(html)


# ============================================================
# 15. EDITORIAL EMPTY STATE
# ============================================================

def render_empty_state(title="No Active Orders", subtitle="Your next market opportunity is waiting on the digital mandi.", action_hint="Browse available produce or post a new requirement."):
    """
    Context-aware editorial empty state.
    """
    html = f"""
    <div style="text-align: center; padding: 36px 20px; background: rgba(255, 255, 255, 0.85); border: 1px dashed rgba(22, 62, 43, 0.2); border-radius: 16px; margin: 18px 0;">
        <div style="font-size: 2.2rem; margin-bottom: 6px;">🌾</div>
        <div style="font-size: 1.2rem; font-weight: 800; color: #163E2B;">{title}</div>
        <div style="font-size: 0.88rem; color: #526058; margin: 6px 0 10px 0;">{subtitle}</div>
        <div style="font-size: 0.82rem; color: #B45309; font-weight: 700;">{action_hint}</div>
    </div>
    """
    render_html(html)


# ============================================================
# 16. PREMIUM TEAM HEXANODES FOOTER (SIH 2026 · PS ID 26033)
# ============================================================

def render_setu_footer():
    """
    Renders the official Team HexaNodes SIH 2026 Problem Statement 26033 footer.
    """
    html = """
    <footer class="setu-master-footer">
        <div class="setu-footer-inner">
            <div class="setu-footer-top-row">
                <div class="setu-footer-brand-side">
                    <div class="setu-footer-logo-badge">
                        <span style="font-size: 1.15rem;">🌾</span>
                        <span class="setu-footer-logo-text">KISAN SETU · किसान सेतू</span>
                    </div>
                    <div class="setu-footer-slogan">National Agro-Economic Intelligence & Unified Digital Mandi Network · 2026</div>
                </div>
                <div class="setu-footer-badges">
                    <span class="setu-badge-sih">🇮🇳 SMART INDIA HACKATHON 2026</span>
                    <span class="setu-badge-ps">PROBLEM STATEMENT ID: 26033</span>
                </div>
            </div>
            <div class="setu-footer-divider"></div>
            <div class="setu-footer-bottom-row">
                <div class="setu-footer-credit">
                    Designed and Implemented by <span class="hexanodes-highlight">Team HexaNodes</span>
                </div>
                <div class="setu-footer-meta">
                    <span>✦ AI Crop Matching</span>
                    <span>✦ Setu Load Dispatch</span>
                    <span>✦ Real-Time Arbitrage Engine</span>
                    <span>✦ Bharat, Reimagined</span>
                </div>
            </div>
        </div>
    </footer>
    """
    render_html(html)


# ============================================================
# 17. LEARNING & PERFORMANCE TELEMETRY SECTION
# ============================================================

def render_learning_performance_section(summary: dict):
    """
    Renders the Feedback -> Learning Loop & Performance section.
    Displays:
    - Transactions analysed
    - Feedback received
    - Match acceptance
    - Completion rate
    - Forecast performance
    - Market realization comparison
    - Mandatory Governance callout: "Feedback is captured for future model evaluation and improvement."
    """
    if not summary:
        return

    st.subheader("🔄 Learning & Performance")
    st.caption("Empirical platform learning telemetry & model evaluation loop")

    # 1. Metric Cards Grid
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)

    tx_cnt = summary.get("transactions_analyzed", 0)
    fb_cnt = summary.get("feedback_received", 0)
    match_acc = summary.get("match_acceptance", {}).get("display_text", "Insufficient data")
    comp_rate = summary.get("completion_rate", {}).get("display_text", "Insufficient data")
    fc_perf = summary.get("forecast_performance", {}).get("display_text", "Insufficient data")
    mkt_real = summary.get("market_realization", {}).get("display_text", "Insufficient data")

    with col1:
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-top: 4px solid #163E2B; border-radius: 10px; padding: 14px 16px; box-shadow: 0 2px 8px rgba(24,32,27,0.03); margin-bottom: 12px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #68756C; text-transform: uppercase;">Transactions Analysed</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #163E2B; margin: 4px 0;">{tx_cnt if tx_cnt > 0 else 'Insufficient data'}</div>
                <div style="font-size: 0.78rem; color: #68756C;">Total platform trade volume</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-top: 4px solid #2D6A4F; border-radius: 10px; padding: 14px 16px; box-shadow: 0 2px 8px rgba(24,32,27,0.03); margin-bottom: 12px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #68756C; text-transform: uppercase;">Feedback Received</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #2D6A4F; margin: 4px 0;">{fb_cnt if fb_cnt > 0 else 'Insufficient data'}</div>
                <div style="font-size: 0.78rem; color: #68756C;">Farmer & buyer evaluations</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-top: 4px solid #1952B3; border-radius: 10px; padding: 14px 16px; box-shadow: 0 2px 8px rgba(24,32,27,0.03); margin-bottom: 12px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #68756C; text-transform: uppercase;">Match Acceptance</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #1952B3; margin: 4px 0;">{match_acc}</div>
                <div style="font-size: 0.78rem; color: #68756C;">Confirmed & in-transit orders</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-top: 4px solid #176536; border-radius: 10px; padding: 14px 16px; box-shadow: 0 2px 8px rgba(24,32,27,0.03); margin-bottom: 12px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #68756C; text-transform: uppercase;">Completion Rate</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #176536; margin: 4px 0;">{comp_rate}</div>
                <div style="font-size: 0.78rem; color: #68756C;">Successfully settled deliveries</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col5:
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-top: 4px solid #E8B83D; border-radius: 10px; padding: 14px 16px; box-shadow: 0 2px 8px rgba(24,32,27,0.03); margin-bottom: 12px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #68756C; text-transform: uppercase;">Forecast Performance</div>
                <div style="font-size: 1.25rem; font-weight: 800; color: #91610A; margin: 4px 0;">{fc_perf}</div>
                <div style="font-size: 0.78rem; color: #68756C;">Out-of-sample demand error</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col6:
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-top: 4px solid #B85C38; border-radius: 10px; padding: 14px 16px; box-shadow: 0 2px 8px rgba(24,32,27,0.03); margin-bottom: 12px;">
                <div style="font-size: 0.72rem; font-weight: 700; color: #68756C; text-transform: uppercase;">Market Realization</div>
                <div style="font-size: 1.25rem; font-weight: 800; color: #B85C38; margin: 4px 0;">{mkt_real}</div>
                <div style="font-size: 0.78rem; color: #68756C;">Realized vs Mandi benchmark</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2. Governance Callout
    governance_box = f'''
    <div style="background: rgba(22, 62, 43, 0.05); border: 1px solid rgba(22, 62, 43, 0.18); border-left: 4px solid #163E2B; border-radius: 8px; padding: 12px 18px; margin-top: 6px; margin-bottom: 12px;">
        <div style="font-weight: 800; color: #163E2B; font-size: 0.9rem;">
            🛡️ {summary.get("learning_note", "Feedback is captured for future model evaluation and improvement.")}
        </div>
        <div style="font-size: 0.8rem; color: #526058; margin-top: 4px;">
            AI Governance Policy: Production model weights remain frozen. No automated weight mutations are executed without verified validation benchmarks.
        </div>
    </div>
    '''
    render_html(governance_box)

