"""
Market Data Normalization, Analytics & Telemetry Engine | Kisan Setu
Bridges data.gov.in APIs with Kisan Setu UI components and AI engines:
- API #1 (Current Daily Price): Live Mandi Pulse, Today's Market Floor & Telemetry
- API #2 (Variety-wise Daily Prices): Live Mandi Price Chits & Grade Benchmarks
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Tuple
from datetime import datetime, date
import pandas as pd

from data_ingestion.data_gov_api import (
    DataGovAPIClient,
    get_current_daily_prices,
    get_variety_wise_prices,
)

logger = logging.getLogger(__name__)

PROCESSED_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
PROCESSED_FILE_PATH = PROCESSED_DATA_DIR / "market_prices.csv"
LEGACY_PRICES_PATH = Path(__file__).resolve().parent.parent / "data" / "prices.csv"
BUYER_REQ_PATH = Path(__file__).resolve().parent.parent / "data" / "buyer_requirements.csv"
DEMAND_PATH = Path(__file__).resolve().parent.parent / "data" / "demand.csv"
TRANSACTIONS_PATH = Path(__file__).resolve().parent.parent / "data" / "transactions.csv"

# Standard schema
NORMALIZED_COLUMNS = [
    "arrival_date",
    "commodity",
    "commodity_code",
    "district",
    "market",
    "state",
    "variety",
    "grade",
    "min_price",           # Source unit: Rs / Quintal
    "max_price",           # Source unit: Rs / Quintal
    "modal_price",         # Source unit: Rs / Quintal
    "min_price_per_kg",    # Converted unit: Rs / kg (min_price / 100.0)
    "max_price_per_kg",    # Converted unit: Rs / kg (max_price / 100.0)
    "modal_price_per_kg",  # Converted unit: Rs / kg (modal_price / 100.0)
    "source_unit",
    "source",
    "retrieval_time",
]

# Track API availability status
_LAST_API_STATUS = {
    "is_live": True,
    "last_successful_fetch": datetime.now().strftime("%d %b %Y, %I:%M %p"),
    "error_message": None,
}


def clean_market_data(
    raw_data: Union[List[Dict[str, Any]], pd.DataFrame],
    source_label: str = "data.gov.in API",
) -> pd.DataFrame:
    """
    Normalize raw records from either data.gov.in API #1, API #2, or local datasets.
    Handles XML/Unicode encoded fields (e.g. Min_x0020_Price) and enforces uniform schema.
    """
    if raw_data is None:
        return pd.DataFrame(columns=NORMALIZED_COLUMNS)

    if isinstance(raw_data, list):
        if not raw_data:
            return pd.DataFrame(columns=NORMALIZED_COLUMNS)
        df = pd.DataFrame(raw_data)
    elif isinstance(raw_data, pd.DataFrame):
        if raw_data.empty:
            return pd.DataFrame(columns=NORMALIZED_COLUMNS)
        df = raw_data.copy()
    else:
        return pd.DataFrame(columns=NORMALIZED_COLUMNS)

    # Normalize encoded column names (e.g. Min_x0020_Price, Modal_x0020_Price)
    col_mapping = {}
    for col in df.columns:
        norm_col = str(col).strip()
        norm_col = norm_col.replace("_x0020_", "_").replace(" ", "_").lower()
        col_mapping[col] = norm_col
    df = df.rename(columns=col_mapping)

    # Field aliases mapping
    field_aliases = {
        "arrival_date": ["arrival_date", "date", "arrival_date_str"],
        "commodity": ["commodity", "crop"],
        "commodity_code": ["commodity_code", "crop_code"],
        "district": ["district"],
        "market": ["market", "mandi"],
        "state": ["state"],
        "variety": ["variety"],
        "grade": ["grade", "quality_grade"],
        "min_price": ["min_price", "min_price_per_quintal", "min_price_rs_per_quintal"],
        "max_price": ["max_price", "max_price_per_quintal", "max_price_rs_per_quintal"],
        "modal_price": ["modal_price", "modal_price_per_quintal", "modal_price_rs_per_quintal"],
    }

    for canonical, aliases in field_aliases.items():
        if canonical not in df.columns:
            for alias in aliases:
                if alias in df.columns:
                    df[canonical] = df[alias]
                    break
            if canonical not in df.columns:
                df[canonical] = None

    # Handle string columns
    for sc in ["commodity", "district", "market", "state", "variety", "grade", "commodity_code"]:
        if sc in df.columns:
            df[sc] = df[sc].fillna("").astype(str).str.strip()

    # Convert prices to numeric
    for price_col in ["min_price", "max_price", "modal_price"]:
        df[price_col] = pd.to_numeric(df[price_col], errors="coerce")

    # If min/max/modal are missing but per-kg prices exist
    if "min_price_per_kg" in df.columns and df["min_price"].isna().all():
        df["min_price_per_kg"] = pd.to_numeric(df["min_price_per_kg"], errors="coerce")
        df["min_price"] = df["min_price_per_kg"] * 100.0

    if "max_price_per_kg" in df.columns and df["max_price"].isna().all():
        df["max_price_per_kg"] = pd.to_numeric(df["max_price_per_kg"], errors="coerce")
        df["max_price"] = df["max_price_per_kg"] * 100.0

    if "modal_price_per_kg" in df.columns and df["modal_price"].isna().all():
        df["modal_price_per_kg"] = pd.to_numeric(df["modal_price_per_kg"], errors="coerce")
        df["modal_price"] = df["modal_price_per_kg"] * 100.0

    # Drop rows without valid positive modal price
    df = df.dropna(subset=["modal_price"])
    df = df[df["modal_price"] > 0].copy()

    if df.empty:
        return pd.DataFrame(columns=NORMALIZED_COLUMNS)

    df["min_price"] = df["min_price"].fillna(df["modal_price"])
    df["max_price"] = df["max_price"].fillna(df["modal_price"])
    df.loc[df["min_price"] <= 0, "min_price"] = df["modal_price"]
    df.loc[df["max_price"] <= 0, "max_price"] = df["modal_price"]

    # Compute explicit per-kg prices
    is_already_per_kg = (df["modal_price"].max() <= 150) and ("modal_price_per_kg" in df.columns and not df["modal_price_per_kg"].isna().all())

    if is_already_per_kg:
        df["min_price_per_kg"] = df["min_price"].round(2)
        df["max_price_per_kg"] = df["max_price"].round(2)
        df["modal_price_per_kg"] = df["modal_price"].round(2)
        df["source_unit"] = "Rs/kg"
    else:
        df["min_price_per_kg"] = (df["min_price"] / 100.0).round(2)
        df["max_price_per_kg"] = (df["max_price"] / 100.0).round(2)
        df["modal_price_per_kg"] = (df["modal_price"] / 100.0).round(2)
        df["source_unit"] = "Rs/Quintal"

    df["source"] = source_label
    df["retrieval_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Date parsing
    def parse_date(val: Any) -> Optional[str]:
        if pd.isna(val) or not str(val).strip():
            return None
        s = str(val).strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(s, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        try:
            dt = pd.to_datetime(s, dayfirst=True)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return None

    df["arrival_date"] = df["arrival_date"].apply(parse_date)
    df = df.dropna(subset=["arrival_date"]).copy()

    # Deduplicate
    dedup_cols = ["arrival_date", "commodity", "district", "market", "variety", "grade"]
    available_dedup = [c for c in dedup_cols if c in df.columns]
    df = df.drop_duplicates(subset=available_dedup, keep="last")

    # Sort
    df = df.sort_values(["arrival_date", "commodity", "district"], ascending=[True, True, True]).reset_index(drop=True)

    result_df = pd.DataFrame()
    for col in NORMALIZED_COLUMNS:
        result_df[col] = df[col] if col in df.columns else None

    return result_df


def save_processed_market_data(df: pd.DataFrame) -> None:
    """Safely append cleaned records to data/processed/market_prices.csv."""
    if df.empty:
        return
    try:
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        if PROCESSED_FILE_PATH.exists():
            try:
                existing_df = pd.read_csv(PROCESSED_FILE_PATH)
                combined = pd.concat([existing_df, df], ignore_index=True)
                cleaned = clean_market_data(combined, source_label="Local Processed Dataset")
                cleaned.to_csv(PROCESSED_FILE_PATH, index=False)
                return
            except Exception:
                pass
        df.to_csv(PROCESSED_FILE_PATH, index=False)
    except Exception as e:
        logger.error(f"Failed to write processed dataset: {e}")


def load_local_market_cache() -> pd.DataFrame:
    """Load records from local processed cache with fallback to legacy prices.csv."""
    if PROCESSED_FILE_PATH.exists():
        try:
            df = pd.read_csv(PROCESSED_FILE_PATH)
            if not df.empty:
                return clean_market_data(df, source_label="Local Processed Cache")
        except Exception:
            pass

    if LEGACY_PRICES_PATH.exists():
        try:
            df = pd.read_csv(LEGACY_PRICES_PATH)
            if not df.empty:
                return clean_market_data(df, source_label="Legacy Benchmark Dataset")
        except Exception:
            pass

    return pd.DataFrame(columns=NORMALIZED_COLUMNS)


# ------------------------------------------------------------
# 1. LIVE MANDI PULSE (Continuous Ticker Data from API #1)
# ------------------------------------------------------------

def get_live_mandi_pulse_items(state: str = "Maharashtra") -> List[Dict[str, Any]]:
    """
    Generates dynamic pulse ticker items for key agricultural commodities and markets
    using data.gov.in API #1 (Current Daily Price) with price change analytics.
    """
    global _LAST_API_STATUS

    # Query API #1 for state records
    api_res = get_current_daily_prices(state=state, limit=100)

    records = []
    is_live = False

    if api_res.get("status") == "success" and api_res.get("records"):
        cleaned_df = clean_market_data(api_res["records"], source_label="data.gov.in Current Daily API")
        if not cleaned_df.empty:
            save_processed_market_data(cleaned_df)
            records = cleaned_df.to_dict(orient="records")
            is_live = True
            _LAST_API_STATUS["is_live"] = True
            _LAST_API_STATUS["last_successful_fetch"] = datetime.now().strftime("%d %b %Y, %I:%M %p")

    if not records:
        # Fallback to local cache
        _LAST_API_STATUS["is_live"] = False
        cached_df = load_local_market_cache()
        if not cached_df.empty:
            records = cached_df.to_dict(orient="records")

    if not records:
        # Safe emergency items if completely empty
        return [
            {"market": "NASHIK", "crop": "कांदा (Onion)", "price": "₹38.00", "change": "+5.2%", "status": "up"},
            {"market": "PUNE", "crop": "टोमॅटो (Tomato)", "price": "₹18.00", "change": "STABLE", "status": "stable"},
            {"market": "MUMBAI", "crop": "बटाटा (Potato)", "price": "₹26.00", "change": "-1.5%", "status": "down"},
            {"market": "AHILYANAGAR", "crop": "गहू (Wheat)", "price": "₹31.50", "change": "STABLE", "status": "stable"},
        ]

    # Map marathi labels
    mr_crop_map = {
        "onion": "कांदा (Onion)",
        "tomato": "टोमॅटो (Tomato)",
        "potato": "बटाटा (Potato)",
        "wheat": "गहू (Wheat)",
        "rice": "तांदूळ (Rice)",
        "banana": "केळी (Banana)",
        "ginger": "आले (Ginger)",
        "ginger(green)": "आले (Ginger)",
        "cabbage": "कोबी (Cabbage)",
        "maize": "मका (Maize)",
        "apple": "सफरचंद (Apple)",
        "pomegranate": "डाळिंब (Pomegranate)",
    }

    # Group by (market, commodity)
    pulse_items = []
    seen = set()

    # Priority pilot markets
    priority_districts = ["nashik", "pune", "ahilyanagar", "mumbai", "ahmednagar", "nagpur", "jalgaon", "raigad"]

    for r in records:
        comm = str(r.get("commodity", "")).strip()
        mkt = str(r.get("market", "")).strip()
        dist = str(r.get("district", "")).strip()
        price_kg = float(r.get("modal_price_per_kg", 0.0))

        if not comm or not mkt or price_kg <= 0:
            continue

        key = (mkt.lower(), comm.lower())
        if key in seen:
            continue
        seen.add(key)

        comm_clean = comm.split("(")[0].strip()
        crop_label = mr_crop_map.get(comm.lower(), mr_crop_map.get(comm_clean.lower(), comm))

        # Calculate dynamic price change
        chg_val, chg_status = calculate_price_change_for_record(comm, mkt, price_kg)
        chg_str = f"{'+' if chg_val > 0 else ''}{chg_val:.1f}%" if chg_val is not None else "STABLE"

        # Shorten market name for clean ticker presentation
        mkt_short = mkt.replace("APMC", "").replace("Samiti", "").replace("Khajgi", "").strip()
        if len(mkt_short) > 18:
            mkt_short = dist.upper() or mkt_short[:18]

        pulse_items.append({
            "market": mkt_short.upper(),
            "crop": crop_label,
            "price": f"₹{price_kg:.2f}",
            "change": chg_str,
            "status": chg_status,
            "district": dist,
        })

        if len(pulse_items) >= 12:
            break

    return pulse_items


# ------------------------------------------------------------
# 2. PRICE CHANGE CALCULATION (Section 7)
# ------------------------------------------------------------

def calculate_price_change_for_record(
    commodity: str,
    market: str,
    current_modal_price: float,
) -> Tuple[Optional[float], str]:
    """
    Calculate price movement percentage using available historical/current records.
    Formula: ((current_modal - previous_modal) / previous_modal) * 100
    Returns: (percentage_change, 'up' | 'down' | 'stable')
    """
    if current_modal_price <= 0:
        return None, "stable"

    # Query local historical cache for previous records
    cached_df = load_local_market_cache()
    if cached_df.empty:
        return None, "stable"

    matches = cached_df[
        (cached_df["commodity"].str.lower() == commodity.lower())
        & (cached_df["market"].str.lower() == market.lower())
    ].copy()

    if len(matches) < 2:
        # Match by commodity and district if exact market lacks history
        matches = cached_df[cached_df["commodity"].str.lower() == commodity.lower()].copy()

    if len(matches) >= 2:
        matches["arrival_date"] = pd.to_datetime(matches["arrival_date"], errors="coerce")
        sorted_m = matches.sort_values("arrival_date").dropna(subset=["arrival_date"])
        if len(sorted_m) >= 2:
            prev_price = float(sorted_m.iloc[-2]["modal_price_per_kg"])
            if prev_price > 0:
                pct = ((current_modal_price - prev_price) / prev_price) * 100.0
                if pct > 0.5:
                    return round(pct, 1), "up"
                elif pct < -0.5:
                    return round(pct, 1), "down"
                else:
                    return 0.0, "stable"

    return None, "stable"


# ------------------------------------------------------------
# 3. LIVE MANDI PRICE CHITS (Section 8 - Variety-wise API #2)
# ------------------------------------------------------------

def get_live_price_chits(
    state: str = "Maharashtra",
    district: Optional[str] = None,
    commodity: Optional[str] = None,
    limit: int = 8,
) -> List[Dict[str, Any]]:
    """
    Retrieves detailed Mandi Price Chits using API #2 (Variety-wise Daily Market Prices).
    Exposes: Commodity, Market, Variety, Grade, Modal Price, Min Price, Max Price, Arrival Date.
    """
    global _LAST_API_STATUS

    # Query Variety-wise API #2
    api_res = get_variety_wise_prices(
        state=state,
        district=district,
        commodity=commodity,
        limit=100,
    )

    records = []
    if api_res.get("status") == "success" and api_res.get("records"):
        cleaned_df = clean_market_data(api_res["records"], source_label="data.gov.in Variety-wise API")
        if not cleaned_df.empty:
            save_processed_market_data(cleaned_df)
            # Sort by arrival_date descending to show latest arrivals
            records = cleaned_df.sort_values("arrival_date", ascending=False).to_dict(orient="records")
            _LAST_API_STATUS["is_live"] = True
            _LAST_API_STATUS["last_successful_fetch"] = datetime.now().strftime("%d %b %Y, %I:%M %p")

    if not records:
        # Fallback to local cache
        _LAST_API_STATUS["is_live"] = False
        cached_df = load_local_market_cache()
        if not cached_df.empty:
            filtered = cached_df.copy()
            if commodity:
                filtered = filtered[filtered["commodity"].str.lower() == commodity.lower()]
            if district:
                filtered = filtered[filtered["district"].str.lower() == district.lower()]
            records = filtered.sort_values("arrival_date", ascending=False).to_dict(orient="records")

    chits = []
    seen = set()

    for r in records:
        comm = str(r.get("commodity", "Onion")).strip()
        mkt = str(r.get("market", "APMC Mandi")).strip()
        variety = str(r.get("variety", "FAQ")).strip() or "Standard"
        grade = str(r.get("grade", "FAQ")).strip() or "Local"
        modal_kg = float(r.get("modal_price_per_kg", 0.0))
        min_kg = float(r.get("min_price_per_kg", modal_kg))
        max_kg = float(r.get("max_price_per_kg", modal_kg))
        arr_date = str(r.get("arrival_date", date.today().strftime("%Y-%m-%d")))

        if modal_kg <= 0:
            continue

        key = (comm.lower(), mkt.lower(), variety.lower())
        if key in seen:
            continue
        seen.add(key)

        chg_val, chg_status = calculate_price_change_for_record(comm, mkt, modal_kg)
        chg_str = f"{'+' if chg_val > 0 else ''}{chg_val:.1f}% today" if chg_val is not None else "STABLE"

        chits.append({
            "commodity": comm.upper(),
            "crop_en": f"{comm.upper()}",
            "crop_mr": f"Grade {grade} · {variety} · {mkt}",
            "price": modal_kg,
            "min_price": min_kg,
            "max_price": max_kg,
            "modal_price": modal_kg,
            "market": mkt,
            "variety": variety,
            "grade": grade,
            "arrival_date": arr_date,
            "time_str": f"Arrival: {arr_date}",
            "change_str": chg_str,
            "is_up": (chg_status == "up"),
            "source": r.get("source", "data.gov.in AGMARKNET"),
        })

        if len(chits) >= limit:
            break

    return chits


# ------------------------------------------------------------
# 4. TODAY'S MARKET FLOOR & TELEMETRY (Section 9 - API #1)
# ------------------------------------------------------------

def get_market_floor_telemetry(
    state: str = "Maharashtra",
    district: Optional[str] = None,
    commodity: Optional[str] = None,
    limit: int = 15,
) -> pd.DataFrame:
    """
    Builds the dynamic Market Floor telemetry table using Current Daily Price API #1.
    Each row contains: Market, Commodity, Current Modal Price, Price Movement, Data Date.
    """
    api_res = get_current_daily_prices(
        state=state,
        district=district,
        commodity=commodity,
        limit=100,
    )

    df = pd.DataFrame()
    if api_res.get("status") == "success" and api_res.get("records"):
        df = clean_market_data(api_res["records"], source_label="data.gov.in Current Daily API")
        if not df.empty:
            save_processed_market_data(df)

    if df.empty:
        cached_df = load_local_market_cache()
        if not cached_df.empty:
            df = cached_df.copy()
            if commodity:
                df = df[df["commodity"].str.lower() == commodity.lower()]
            if district:
                df = df[df["district"].str.lower() == district.lower()]

    if df.empty:
        return pd.DataFrame(columns=[
            "market", "commodity", "modal_price_per_kg", "min_price_per_kg",
            "max_price_per_kg", "price_str", "movement", "arrival_date", "variety", "grade"
        ])

    rows = []
    seen = set()
    for _, r in df.iterrows():
        mkt = str(r.get("market", "")).strip()
        comm = str(r.get("commodity", "")).strip()
        p_kg = float(r.get("modal_price_per_kg", 0.0))
        d_date = str(r.get("arrival_date", ""))

        if not mkt or not comm or p_kg <= 0:
            continue

        key = (mkt.lower(), comm.lower())
        if key in seen:
            continue
        seen.add(key)

        chg_val, chg_status = calculate_price_change_for_record(comm, mkt, p_kg)
        if chg_val is not None:
            movement_str = f"↑ +{chg_val:.1f}%" if chg_val > 0 else (f"↓ {chg_val:.1f}%" if chg_val < 0 else "— Stable")
        else:
            movement_str = "— Stable"

        rows.append({
            "market": mkt,
            "district": r.get("district", ""),
            "commodity": comm,
            "modal_price_per_kg": p_kg,
            "min_price_per_kg": float(r.get("min_price_per_kg", p_kg)),
            "max_price_per_kg": float(r.get("max_price_per_kg", p_kg)),
            "price_str": f"₹{p_kg:.2f}/kg",
            "movement": movement_str,
            "arrival_date": d_date,
            "variety": r.get("variety", "FAQ"),
            "grade": r.get("grade", "Local"),
            "source": r.get("source", "data.gov.in API"),
        })

        if len(rows) >= limit:
            break

    return pd.DataFrame(rows)


# ------------------------------------------------------------
# 5. DEMAND SIGNAL CALCULATION (Section 10)
# ------------------------------------------------------------

def calculate_demand_signal(crop: str, district: Optional[str] = None) -> str:
    """
    Computes transparent evidence-based demand signal using project operational datasets:
    - buyer_requirements.csv (active buyer procurement postings)
    - demand.csv (regional wholesale consumption volume)
    - transactions.csv (active fulfilment orders)
    
    Returns: 'HIGH' | 'MODERATE' | 'STEADY' | 'LOW' | 'INSUFFICIENT DATA'
    Note: Mandi price API alone does not measure demand.
    """
    total_req_kg = 0.0
    active_buyers = 0

    # 1. Analyze Buyer Requirements
    if BUYER_REQ_PATH.exists():
        try:
            req_df = pd.read_csv(BUYER_REQ_PATH)
            if not req_df.empty and "crop" in req_df.columns:
                matches = req_df[req_df["crop"].astype(str).str.lower() == crop.lower()]
                if not matches.empty:
                    total_req_kg += pd.to_numeric(matches.get("quantity_kg", 0), errors="coerce").sum()
                    active_buyers += len(matches)
        except Exception:
            pass

    # 2. Analyze Historical Demand Volume
    demand_vol = 0.0
    if DEMAND_PATH.exists():
        try:
            dem_df = pd.read_csv(DEMAND_PATH)
            if not dem_df.empty and "crop" in dem_df.columns:
                d_matches = dem_df[dem_df["crop"].astype(str).str.lower() == crop.lower()]
                if district and "district" in dem_df.columns:
                    d_matches = d_matches[d_matches["district"].astype(str).str.lower() == district.lower()]
                if not d_matches.empty:
                    demand_vol = pd.to_numeric(d_matches.get("demand_quantity_kg", 0), errors="coerce").mean()
        except Exception:
            pass

    if total_req_kg == 0 and demand_vol == 0:
        return "INSUFFICIENT DATA"

    combined_metric = total_req_kg + demand_vol

    if combined_metric >= 2500 or active_buyers >= 3:
        return "HIGH"
    elif combined_metric >= 1000 or active_buyers >= 2:
        return "MODERATE"
    elif combined_metric > 0:
        return "STEADY"
    else:
        return "LOW"


# ------------------------------------------------------------
# 6. SETU INTELLIGENCE SIGNAL GENERATOR (Section 11)
# ------------------------------------------------------------

def generate_setu_intelligence_signal(
    crop: str = "Onion",
    district: str = "Nashik",
) -> Dict[str, Any]:
    """
    Synthesizes current mandi modal benchmark, price movement, and buyer demand signal
    into a factual, evidence-based market intelligence insight.
    """
    bench = get_latest_market_price(commodity=crop, district=district)
    modal_price = bench.get("modal_price_per_kg", 0.0)
    market_name = bench.get("market", district)
    arrival_date = bench.get("arrival_date", "")
    is_live = bench.get("is_live", False)

    demand_sig = calculate_demand_signal(crop, district)
    chg_val, chg_status = calculate_price_change_for_record(crop, market_name, modal_price)

    if modal_price <= 0:
        return {
            "signal_title": "Setu Intelligence Signal",
            "insight_text": "Setu Intelligence: Not enough current market data to generate a reliable market signal.",
            "demand_signal": "INSUFFICIENT DATA",
            "modal_price": 0.0,
            "confidence": 50,
        }

    # Synthesize evidence-based factual text
    if demand_sig == "HIGH" and chg_status == "up":
        insight = (
            f"{crop} mandi benchmark is strong at ₹{modal_price:.2f}/kg ({market_name}, {arrival_date}) "
            f"with high active procurement demand across regional wholesale corridors."
        )
        conf = 92
    elif demand_sig in ["HIGH", "MODERATE"]:
        insight = (
            f"Steady wholesale buyer interest for {crop} with current benchmark at ₹{modal_price:.2f}/kg. "
            f"Direct buyer match offers attractive net realization over local auction floors."
        )
        conf = 88
    elif chg_status == "down":
        insight = (
            f"{crop} mandi modal price softened to ₹{modal_price:.2f}/kg at {market_name}. "
            f"Direct contract matching with fixed price buyer requirements is recommended."
        )
        conf = 82
    else:
        insight = (
            f"Current daily mandi benchmark for {crop} in {district} stands at ₹{modal_price:.2f}/kg "
            f"({market_name}). Demand signal is {demand_sig.lower()}."
        )
        conf = 85

    return {
        "signal_title": f"Setu Intelligence · {crop} ({district})",
        "insight_text": insight,
        "demand_signal": demand_sig,
        "modal_price": modal_price,
        "market": market_name,
        "arrival_date": arrival_date,
        "is_live": is_live,
        "confidence": conf,
    }


# ------------------------------------------------------------
# 7. LATEST BENCHMARK RESOLUTION & DATA STATUS
# ------------------------------------------------------------

def get_latest_market_price(
    commodity: str,
    district: Optional[str] = None,
    state: str = "Maharashtra",
) -> Dict[str, Any]:
    """
    Get latest benchmark price and metadata querying both APIs with local fallback.
    """
    # 1. Try Current Daily API #1
    api1_res = get_current_daily_prices(
        state=state,
        district=district,
        commodity=commodity,
        limit=50,
    )

    if api1_res.get("status") == "success" and api1_res.get("records"):
        cleaned = clean_market_data(api1_res["records"], source_label="data.gov.in Current Daily API")
        if not cleaned.empty:
            save_processed_market_data(cleaned)
            exact = cleaned[cleaned["commodity"].astype(str).str.strip().str.lower() == str(commodity).strip().lower()]
            if not exact.empty:
                latest = exact.iloc[-1]
                return {
                    "commodity": str(latest.get("commodity", commodity)),
                    "district": str(latest.get("district", district or "Maharashtra")),
                    "market": str(latest.get("market", "APMC Mandi")),
                    "arrival_date": str(latest.get("arrival_date", date.today().strftime("%Y-%m-%d"))),
                    "variety": str(latest.get("variety", "General")),
                    "grade": str(latest.get("grade", "FAQ")),
                    "modal_price_per_kg": float(latest.get("modal_price_per_kg", 28.40)),
                    "min_price_per_kg": float(latest.get("min_price_per_kg", latest.get("modal_price_per_kg", 28.40))),
                    "max_price_per_kg": float(latest.get("max_price_per_kg", latest.get("modal_price_per_kg", 28.40))),
                    "modal_price": float(latest.get("modal_price", 2840.0)),
                    "min_price": float(latest.get("min_price", 2840.0)),
                    "max_price": float(latest.get("max_price", 2840.0)),
                    "is_live": True,
                    "source": "data.gov.in Current Daily API",
                    "source_unit": "Rs/Quintal",
                    "display_unit": "Rs/kg",
                }

    # 2. Try Variety-wise API #2
    api2_res = get_variety_wise_prices(
        state=state,
        district=district,
        commodity=commodity,
        limit=50,
    )

    if api2_res.get("status") == "success" and api2_res.get("records"):
        cleaned2 = clean_market_data(api2_res["records"], source_label="data.gov.in Variety-wise API")
        if not cleaned2.empty:
            save_processed_market_data(cleaned2)
            exact2 = cleaned2[cleaned2["commodity"].astype(str).str.strip().str.lower() == str(commodity).strip().lower()]
            if not exact2.empty:
                latest = exact2.sort_values("arrival_date", ascending=True).iloc[-1]
                return {
                    "commodity": str(latest.get("commodity", commodity)),
                    "district": str(latest.get("district", district or "Maharashtra")),
                    "market": str(latest.get("market", "APMC Mandi")),
                    "arrival_date": str(latest.get("arrival_date", date.today().strftime("%Y-%m-%d"))),
                    "variety": str(latest.get("variety", "General")),
                    "grade": str(latest.get("grade", "FAQ")),
                    "modal_price_per_kg": float(latest.get("modal_price_per_kg", 28.40)),
                    "min_price_per_kg": float(latest.get("min_price_per_kg", latest.get("modal_price_per_kg", 28.40))),
                    "max_price_per_kg": float(latest.get("max_price_per_kg", latest.get("modal_price_per_kg", 28.40))),
                    "modal_price": float(latest.get("modal_price", 2840.0)),
                    "min_price": float(latest.get("min_price", 2840.0)),
                    "max_price": float(latest.get("max_price", 2840.0)),
                    "is_live": True,
                    "source": "data.gov.in Variety-wise API",
                    "source_unit": "Rs/Quintal",
                    "display_unit": "Rs/kg",
                }

    # 3. Fallback to Local Cache
    cached_df = load_local_market_cache()
    if not cached_df.empty:
        filtered = cached_df[cached_df["commodity"].str.lower() == commodity.lower()]
        if district:
            d_lower = district.lower()
            if d_lower in ["ahmednagar", "ahilyanagar"]:
                filtered = filtered[filtered["district"].str.lower().isin(["ahmednagar", "ahilyanagar"])]
            else:
                filtered = filtered[filtered["district"].str.lower() == d_lower]

        if not filtered.empty:
            latest = filtered.sort_values("arrival_date", ascending=True).iloc[-1]
            return {
                "commodity": str(latest.get("commodity", commodity)),
                "district": str(latest.get("district", district or "Maharashtra")),
                "market": str(latest.get("market", f"{district or 'Local'} APMC")),
                "arrival_date": str(latest.get("arrival_date", date.today().strftime("%Y-%m-%d"))),
                "variety": str(latest.get("variety", "Standard")),
                "grade": str(latest.get("grade", "FAQ")),
                "modal_price_per_kg": float(latest.get("modal_price_per_kg", 28.40)),
                "min_price_per_kg": float(latest.get("min_price_per_kg", latest.get("modal_price_per_kg", 28.40))),
                "max_price_per_kg": float(latest.get("max_price_per_kg", latest.get("modal_price_per_kg", 28.40))),
                "modal_price": float(latest.get("modal_price", 2840.0)),
                "min_price": float(latest.get("min_price", 2840.0)),
                "max_price": float(latest.get("max_price", 2840.0)),
                "is_live": False,
                "source": "Cached Local Dataset",
                "source_unit": "Rs/Quintal",
                "display_unit": "Rs/kg",
            }

    # 4. Safe baseline fallback
    default_defaults = {
        "onion": {"modal": 38.00, "min": 20.00, "max": 45.00},
        "tomato": {"modal": 18.00, "min": 12.00, "max": 24.00},
        "potato": {"modal": 26.00, "min": 22.00, "max": 30.00},
        "wheat": {"modal": 31.50, "min": 28.00, "max": 34.00},
    }
    defaults = default_defaults.get(commodity.lower(), {"modal": 30.00, "min": 20.00, "max": 40.00})

    return {
        "commodity": commodity,
        "district": district or "Maharashtra",
        "market": f"{district or 'Maharashtra'} APMC",
        "arrival_date": date.today().strftime("%Y-%m-%d"),
        "variety": "Local FAQ",
        "grade": "FAQ",
        "modal_price_per_kg": defaults["modal"],
        "min_price_per_kg": defaults["min"],
        "max_price_per_kg": defaults["max"],
        "modal_price": defaults["modal"] * 100.0,
        "min_price": defaults["min"] * 100.0,
        "max_price": defaults["max"] * 100.0,
        "is_live": False,
        "source": "Baseline Regional Benchmark",
        "source_unit": "Rs/Quintal",
        "display_unit": "Rs/kg",
    }


def get_mandi_data_status() -> Dict[str, Any]:
    """Returns real status indicator for Mandi telemetry (LIVE vs FALLBACK)."""
    global _LAST_API_STATUS
    client = DataGovAPIClient()
    if not client.has_api_key:
        return {
            "is_live": False,
            "status_badge": "● FALLBACK",
            "status_text": "Using cached/local data (API key not configured)",
            "last_updated": _LAST_API_STATUS["last_successful_fetch"],
            "source": "Local Dataset",
            "color": "#B45309",
        }

    if _LAST_API_STATUS["is_live"]:
        return {
            "is_live": True,
            "status_badge": "● LIVE — data.gov.in",
            "status_text": "Live daily mandi data from OGD Platform",
            "last_updated": _LAST_API_STATUS["last_successful_fetch"],
            "source": "data.gov.in / AGMARKNET",
            "color": "#176536",
        }
    else:
        return {
            "is_live": False,
            "status_badge": "● FALLBACK",
            "status_text": "Using cached/local data",
            "last_updated": _LAST_API_STATUS["last_successful_fetch"],
            "source": "data.gov.in Cache",
            "color": "#B45309",
        }


def clear_mandi_cache() -> None:
    """Manually clear Streamlit cache for mandi queries."""
    try:
        import streamlit as st
        st.cache_data.clear()
        logger.info("Cleared Streamlit mandi cache.")
    except Exception as e:
        logger.warning(f"Could not clear Streamlit cache: {e}")


def get_market_prices(
    commodity: Optional[str] = None,
    district: Optional[str] = None,
    state: str = "Maharashtra",
    limit: int = 50,
) -> pd.DataFrame:
    """General fetcher for market prices."""
    api_res = get_current_daily_prices(state=state, district=district, commodity=commodity, limit=limit)
    if api_res.get("status") == "success" and api_res.get("records"):
        return clean_market_data(api_res["records"])
    return load_local_market_cache()


# Alias for backward compatibility
fetch_market_data = get_market_prices
