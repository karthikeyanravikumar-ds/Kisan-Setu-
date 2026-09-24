"""
Kisan Setu Editorial Data Visualizations
Theme: 'Bharat, Reimagined'
Minimal gridlines, clear typography, meaningful annotations, no rainbow palettes.
"""

try:
    import plotly.graph_objects as go
    import plotly.express as px
except ImportError:
    go = None
    px = None
import pandas as pd


# Color Palette
CHART_NEEM = "#183A2A"
CHART_FOREST = "#214C37"
CHART_HALDI = "#E8B83D"
CHART_MITTI = "#B85C38"
CHART_TERRACOTTA = "#9E4932"
CHART_JOWAR = "#D7B982"
CHART_INK = "#18201B"
CHART_MUTED = "#68756C"
CHART_BORDER = "#E5DFD3"
CHART_BG = "rgba(0,0,0,0)"


def apply_editorial_layout(fig, title="", subtitle="", height=360):
    """
    Applies the Kisan Setu editorial styling to any Plotly figure.
    Generous spacing ensures title, subtitle, and legend never overlap.
    """
    fig.update_layout(
        title={
            "text": f"<b>{title}</b><br><span style='font-size:12px; color:{CHART_MUTED}; font-weight:normal;'>{subtitle}</span>" if subtitle else f"<b>{title}</b>",
            "font": {"family": "Plus Jakarta Sans, Manrope, sans-serif", "size": 15, "color": CHART_NEEM},
            "x": 0.01,
            "y": 0.98,
            "xanchor": "left",
            "yanchor": "top",
        },
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font={"family": "Plus Jakarta Sans, Manrope, sans-serif", "color": CHART_INK, "size": 12},
        margin={"l": 40, "r": 30, "t": 75, "b": 55},
        height=height,
        hoverlabel={
            "bgcolor": "#FFFFFF",
            "bordercolor": CHART_BORDER,
            "font": {"family": "Plus Jakarta Sans, sans-serif", "size": 12, "color": CHART_INK}
        },
        xaxis={
            "showgrid": False,
            "linecolor": CHART_BORDER,
            "tickcolor": CHART_BORDER,
            "tickfont": {"size": 11, "color": CHART_MUTED},
        },
        yaxis={
            "showgrid": True,
            "gridcolor": "rgba(229, 223, 211, 0.6)",
            "gridwidth": 1,
            "linecolor": "rgba(0, 0, 0, 0)",
            "tickfont": {"size": 11, "color": CHART_MUTED},
            "zeroline": False,
        },
        legend={
            "orientation": "h",
            "yanchor": "top",
            "y": -0.15,
            "xanchor": "center",
            "x": 0.5,
            "font": {"size": 11, "color": CHART_MUTED}
        }
    )
    return fig


def create_mandi_trend_chart(prices_df, crop="Onion", market="Nashik"):
    """
    Generates a high-trust price movement chart.
    Handles both 'arrival_date' (data.gov.in) and 'date' (legacy dataset).
    """
    if go is None or prices_df is None or prices_df.empty:
        return None

    c_col = "commodity" if "commodity" in prices_df.columns else "crop"
    d_col = "arrival_date" if "arrival_date" in prices_df.columns else ("date" if "date" in prices_df.columns else None)

    if c_col not in prices_df.columns or d_col is None:
        return None

    filtered = prices_df[
        (prices_df[c_col].astype(str).str.lower() == crop.lower()) &
        (prices_df["market"].astype(str).str.lower() == market.lower())
    ].copy()

    if filtered.empty:
        filtered = prices_df[prices_df[c_col].astype(str).str.lower() == crop.lower()].copy()

    if filtered.empty:
        return None

    filtered["plot_date"] = pd.to_datetime(filtered[d_col], errors="coerce")
    filtered = filtered.dropna(subset=["plot_date"]).sort_values("plot_date")

    if filtered.empty:
        return None

    m_col = "modal_price_per_kg" if "modal_price_per_kg" in filtered.columns else ("modal_price" if "modal_price" in filtered.columns else None)
    if not m_col:
        return None

    modal_values = pd.to_numeric(filtered[m_col], errors="coerce")
    if modal_values.max() > 150 and m_col == "modal_price":
        modal_values = modal_values / 100.0

    fig = go.Figure()

    # Modal Price Line
    fig.add_trace(go.Scatter(
        x=filtered["plot_date"],
        y=modal_values,
        mode="lines+markers",
        name="Modal Price (आजचा भाव)",
        line={"color": CHART_NEEM, "width": 3},
        marker={"size": 6, "color": CHART_NEEM},
        fill="tozeroy",
        fillcolor="rgba(24, 58, 42, 0.06)"
    ))

    # High / Low Spread bounds if present
    max_col = "max_price_per_kg" if "max_price_per_kg" in filtered.columns else ("max_price" if "max_price" in filtered.columns else None)
    min_col = "min_price_per_kg" if "min_price_per_kg" in filtered.columns else ("min_price" if "min_price" in filtered.columns else None)

    if max_col and min_col:
        max_vals = pd.to_numeric(filtered[max_col], errors="coerce")
        min_vals = pd.to_numeric(filtered[min_col], errors="coerce")
        if max_vals.max() > 150 and max_col == "max_price":
            max_vals = max_vals / 100.0
        if min_vals.max() > 150 and min_col == "min_price":
            min_vals = min_vals / 100.0

        fig.add_trace(go.Scatter(
            x=filtered["plot_date"],
            y=max_vals,
            mode="lines",
            name="Mandi High (कमाल)",
            line={"color": CHART_HALDI, "width": 1.5, "dash": "dot"},
        ))
        fig.add_trace(go.Scatter(
            x=filtered["plot_date"],
            y=min_vals,
            mode="lines",
            name="Mandi Low (किमान)",
            line={"color": CHART_MITTI, "width": 1.5, "dash": "dot"},
        ))

    apply_editorial_layout(
        fig,
        title=f"{crop} Price Momentum · {market}",
        subtitle="Daily modal realization trend across major auctions (₹/kg)"
    )
    return fig


def create_supply_demand_chart(demand_df, produce_df, crop="Onion"):
    """
    Visualizes regional balance between available harvest and buyer requirement.
    """
    if go is None:
        return None

    districts = ["Nashik", "Ahmednagar", "Pune"]

    supply_data = []
    demand_data = []

    for dist in districts:
        sup = produce_df[
            (produce_df["crop"].str.lower() == crop.lower()) &
            (produce_df["district"].str.lower() == dist.lower())
        ]["quantity_kg"].sum() if not produce_df.empty else 0

        dem = demand_df[
            (demand_df["crop"].str.lower() == crop.lower()) &
            (demand_df["district"].str.lower() == dist.lower())
        ]["demand_quantity_kg"].sum() if not demand_df.empty else 0

        supply_data.append(sup)
        demand_data.append(dem)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=districts,
        y=supply_data,
        name="Farm Supply (उपलब्ध आवक)",
        marker_color=CHART_NEEM,
        width=0.28
    ))
    fig.add_trace(go.Bar(
        x=districts,
        y=demand_data,
        name="Buyer Demand (मागणी)",
        marker_color=CHART_TERRACOTTA,
        width=0.28
    ))

    apply_editorial_layout(
        fig,
        title=f"{crop} Regional Equilibrium (आवक vs मागणी)",
        subtitle="Comparison of active farm inventory against wholesale order demand (kg)"
    )
    fig.update_layout(barmode="group")
    return fig
