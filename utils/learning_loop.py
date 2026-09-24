"""
Feedback -> Learning Loop & Performance Analytics Engine | Kisan Setu
Theme: 'Bharat, Reimagined'

Computes empirical platform performance and closed-loop feedback telemetry:
1. Match Acceptance Rate
2. Transaction Completion Rate
3. Farmer & Buyer Feedback Summaries
4. Realized Price vs Mandi Benchmark Comparison
5. Demand Forecast Error (MAE, RMSE, MAPE) via Chronological Evaluation
6. Quality-Assistance Feedback & Grade Telemetry

GOVERNANCE & SAFETY:
- Does NOT automatically modify model weights.
- Does NOT claim that the model has retrained.
- Uses explicit label: "Feedback is captured for future model evaluation and improvement."
- Handles missing or sparse data gracefully with "Insufficient data".
"""

import os
import sys
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List

# Ensure project root is available for imports
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from utils.data_loader import (
    load_transactions,
    load_feedback,
    load_produce,
    load_prices,
    load_demand,
)
from utils.demand_data import build_transaction_demand_history
from ai.demand_forecasting import forecast_demand

LEARNING_NOTE = "Feedback is captured for future model evaluation and improvement."
NO_RETRAIN_NOTE = "Production model weights preserved. No automated parameter mutation."


def calculate_match_acceptance(transactions_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Calculates match acceptance rate from transactions.
    Accepted statuses include: Confirmed, In Transit, Delivered, Completed.
    Pending/Initial: Order Placed.
    Rejected/Cancelled: Cancelled, Rejected.
    """
    if transactions_df is None:
        transactions_df = load_transactions()

    if (
        transactions_df is None
        or not isinstance(transactions_df, pd.DataFrame)
        or transactions_df.empty
        or "status" not in transactions_df.columns
    ):
        return {
            "total_matches": 0,
            "accepted_matches": 0,
            "rejected_matches": 0,
            "pending_matches": 0,
            "acceptance_rate_pct": None,
            "display_text": "Insufficient data",
        }

    valid_df = transactions_df.dropna(subset=["status"]).copy()
    if valid_df.empty:
        return {
            "total_matches": 0,
            "accepted_matches": 0,
            "rejected_matches": 0,
            "pending_matches": 0,
            "acceptance_rate_pct": None,
            "display_text": "Insufficient data",
        }

    status_series = valid_df["status"].astype(str).str.strip().str.lower()
    total = len(status_series)
    if total == 0:
        return {
            "total_matches": 0,
            "accepted_matches": 0,
            "rejected_matches": 0,
            "pending_matches": 0,
            "acceptance_rate_pct": None,
            "display_text": "Insufficient data",
        }

    accepted_statuses = {"confirmed", "in transit", "delivered", "completed"}
    rejected_statuses = {"cancelled", "rejected", "declined"}
    pending_statuses = {"order placed", "pending", "requested"}

    accepted = int(status_series.isin(accepted_statuses).sum())
    rejected = int(status_series.isin(rejected_statuses).sum())
    pending = int(status_series.isin(pending_statuses).sum())

    # Acceptance rate calculation
    rate_pct = round((accepted / total) * 100.0, 1)

    return {
        "total_matches": total,
        "accepted_matches": accepted,
        "rejected_matches": rejected,
        "pending_matches": pending,
        "acceptance_rate_pct": rate_pct,
        "display_text": f"{rate_pct:.1f}%",
    }


def calculate_transaction_completion(transactions_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Calculates transaction completion rate from transactions.
    Completed statuses: Delivered, Completed.
    """
    if transactions_df is None:
        transactions_df = load_transactions()

    if (
        transactions_df is None
        or not isinstance(transactions_df, pd.DataFrame)
        or transactions_df.empty
        or "status" not in transactions_df.columns
    ):
        return {
            "total_transactions": 0,
            "completed_transactions": 0,
            "in_transit_transactions": 0,
            "completion_rate_pct": None,
            "display_text": "Insufficient data",
        }

    valid_df = transactions_df.dropna(subset=["status"]).copy()
    if valid_df.empty:
        return {
            "total_transactions": 0,
            "completed_transactions": 0,
            "in_transit_transactions": 0,
            "completion_rate_pct": None,
            "display_text": "Insufficient data",
        }

    status_series = valid_df["status"].astype(str).str.strip().str.lower()
    total = len(status_series)
    if total == 0:
        return {
            "total_transactions": 0,
            "completed_transactions": 0,
            "in_transit_transactions": 0,
            "completion_rate_pct": None,
            "display_text": "Insufficient data",
        }

    completed_statuses = {"delivered", "completed"}
    in_transit_statuses = {"in transit"}

    completed = int(status_series.isin(completed_statuses).sum())
    in_transit = int(status_series.isin(in_transit_statuses).sum())

    rate_pct = round((completed / total) * 100.0, 1)

    return {
        "total_transactions": total,
        "completed_transactions": completed,
        "in_transit_transactions": in_transit,
        "completion_rate_pct": rate_pct,
        "display_text": f"{rate_pct:.1f}%",
    }


def calculate_feedback_summary(feedback_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Computes farmer and buyer feedback telemetry including average ratings and comments.
    """
    if feedback_df is None:
        feedback_df = load_feedback()

    default_res = {
        "total_feedback_count": 0,
        "farmer": {
            "count": 0,
            "avg_rating": None,
            "display_rating": "Insufficient data",
            "comments": [],
        },
        "buyer": {
            "count": 0,
            "avg_rating": None,
            "display_rating": "Insufficient data",
            "comments": [],
        },
        "all_feedback": [],
    }

    if feedback_df is None or not isinstance(feedback_df, pd.DataFrame) or feedback_df.empty:
        return default_res

    required_cols = {"user_type", "rating"}
    if not required_cols.issubset(feedback_df.columns):
        return default_res

    df = feedback_df.copy()
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df = df.dropna(subset=["rating", "user_type"])

    if df.empty:
        return default_res

    total_count = len(df)
    comments_col = "comment" if "comment" in df.columns else None

    # Farmer slice
    farmer_df = df[df["user_type"].astype(str).str.strip().str.lower() == "farmer"]
    f_count = len(farmer_df)
    f_avg = round(float(farmer_df["rating"].mean()), 1) if f_count > 0 else None
    f_comments = (
        farmer_df[comments_col].dropna().astype(str).tolist()
        if comments_col and f_count > 0
        else []
    )

    # Buyer slice
    buyer_df = df[df["user_type"].astype(str).str.strip().str.lower() == "buyer"]
    b_count = len(buyer_df)
    b_avg = round(float(buyer_df["rating"].mean()), 1) if b_count > 0 else None
    b_comments = (
        buyer_df[comments_col].dropna().astype(str).tolist()
        if comments_col and b_count > 0
        else []
    )

    all_records = []
    for _, row in df.iterrows():
        all_records.append({
            "feedback_id": str(row.get("feedback_id", "")),
            "user_type": str(row.get("user_type", "")),
            "user_id": str(row.get("user_id", "")),
            "transaction_id": str(row.get("transaction_id", "")),
            "rating": float(row.get("rating", 0.0)),
            "comment": str(row.get("comment", "")),
        })

    return {
        "total_feedback_count": total_count,
        "farmer": {
            "count": f_count,
            "avg_rating": f_avg,
            "display_rating": f"{f_avg:.1f} / 5.0" if f_avg is not None else "Insufficient data",
            "comments": f_comments,
        },
        "buyer": {
            "count": b_count,
            "avg_rating": b_avg,
            "display_rating": f"{b_avg:.1f} / 5.0" if b_avg is not None else "Insufficient data",
            "comments": b_comments,
        },
        "all_feedback": all_records,
    }


def calculate_market_realization_comparison(
    transactions_df: Optional[pd.DataFrame] = None,
    produce_df: Optional[pd.DataFrame] = None,
    prices_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """
    Calculates realized transaction prices against matching live/historical mandi modal prices.
    """
    if transactions_df is None:
        transactions_df = load_transactions()
    if produce_df is None:
        produce_df = load_produce()
    if prices_df is None:
        prices_df = load_prices()

    default_res = {
        "transactions_compared": 0,
        "avg_realized_price": None,
        "avg_mandi_benchmark": None,
        "avg_premium_per_kg": None,
        "avg_premium_pct": None,
        "display_text": "Insufficient data",
        "spread_details": [],
    }

    if (
        transactions_df is None
        or produce_df is None
        or prices_df is None
        or transactions_df.empty
        or produce_df.empty
        or prices_df.empty
    ):
        return default_res

    # Validate columns
    tx_req = {"transaction_id", "produce_id", "price_per_kg"}
    pr_req = {"produce_id", "crop"}
    mk_req = {"crop", "modal_price_per_kg"}

    if not tx_req.issubset(transactions_df.columns) or not pr_req.issubset(produce_df.columns):
        return default_res

    # Prepare transactions joined with produce
    tx = transactions_df.copy()
    tx["price_per_kg"] = pd.to_numeric(tx["price_per_kg"], errors="coerce")
    tx = tx.dropna(subset=["price_per_kg", "produce_id"])
    if tx.empty:
        return default_res

    pr = produce_df[["produce_id", "crop"] + (["district"] if "district" in produce_df.columns else [])].copy()
    merged = pd.merge(tx, pr, on="produce_id", how="inner")
    if merged.empty:
        return default_res

    # Prepare Mandi Benchmarks (average modal price by crop and district if available)
    mk = prices_df.copy()
    if "modal_price_per_kg" not in mk.columns or "crop" not in mk.columns:
        return default_res

    mk["modal_price_per_kg"] = pd.to_numeric(mk["modal_price_per_kg"], errors="coerce")
    mk = mk.dropna(subset=["modal_price_per_kg", "crop"])
    if mk.empty:
        return default_res

    # Group mandi prices by crop (and district if present)
    mk["crop_norm"] = mk["crop"].astype(str).str.strip().str.lower()
    crop_benchmarks = mk.groupby("crop_norm")["modal_price_per_kg"].mean().to_dict()

    spread_details = []
    realized_prices = []
    mandi_benchmarks = []

    for _, row in merged.iterrows():
        crop_val = str(row.get("crop", "")).strip()
        crop_key = crop_val.lower()
        if crop_key in crop_benchmarks:
            r_price = float(row["price_per_kg"])
            m_price = float(crop_benchmarks[crop_key])
            diff = r_price - m_price
            diff_pct = (diff / m_price) * 100.0 if m_price > 0 else 0.0

            realized_prices.append(r_price)
            mandi_benchmarks.append(m_price)
            spread_details.append({
                "transaction_id": str(row.get("transaction_id", "")),
                "crop": crop_val,
                "realized_price": round(r_price, 2),
                "mandi_modal_price": round(m_price, 2),
                "difference_per_kg": round(diff, 2),
                "difference_pct": round(diff_pct, 1),
            })

    if not realized_prices:
        return default_res

    avg_realized = round(float(np.mean(realized_prices)), 2)
    avg_mandi = round(float(np.mean(mandi_benchmarks)), 2)
    avg_prem = round(avg_realized - avg_mandi, 2)
    avg_prem_pct = round((avg_prem / avg_mandi) * 100.0, 1) if avg_mandi > 0 else 0.0

    sign = "+" if avg_prem >= 0 else ""
    display_str = f"{sign}₹{avg_prem:.2f}/kg ({sign}{avg_prem_pct:.1f}%) vs Mandi"

    return {
        "transactions_compared": len(realized_prices),
        "avg_realized_price": avg_realized,
        "avg_mandi_benchmark": avg_mandi,
        "avg_premium_per_kg": avg_prem,
        "avg_premium_pct": avg_prem_pct,
        "display_text": display_str,
        "spread_details": spread_details,
    }


def calculate_forecast_performance(
    demand_df: Optional[pd.DataFrame] = None,
    transactions_df: Optional[pd.DataFrame] = None,
    produce_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """
    Evaluates out-of-sample forecast accuracy across standard regional benchmarks
    using strict chronological splits.
    """
    if demand_df is None:
        demand_df = load_demand()
    if transactions_df is None:
        transactions_df = load_transactions()
    if produce_df is None:
        produce_df = load_produce()

    default_res = {
        "series_evaluated": 0,
        "avg_mae": None,
        "avg_rmse": None,
        "avg_mape": None,
        "display_text": "Insufficient data",
        "series_results": [],
    }

    # Evaluate target series
    targets = [
        {"district": "Pune", "crop": "Onion", "df": demand_df, "test_size": 2},
        {"district": "Pune", "crop": "Tomato", "df": demand_df, "test_size": 2},
    ]

    # Add transaction-derived series if possible
    if transactions_df is not None and produce_df is not None and not transactions_df.empty and not produce_df.empty:
        try:
            tx_demand = build_transaction_demand_history(transactions_df, produce_df)
            if not tx_demand.empty:
                targets.append({"district": "Nashik", "crop": "Onion", "df": tx_demand, "test_size": 1})
        except Exception:
            pass

    series_results = []
    maes = []
    rmses = []
    mapes = []

    for tgt in targets:
        df_tgt = tgt["df"]
        if df_tgt is None or not isinstance(df_tgt, pd.DataFrame) or df_tgt.empty:
            continue

        d_clean = tgt["district"].strip().lower()
        c_clean = tgt["crop"].strip().lower()

        if "district" not in df_tgt.columns or "crop" not in df_tgt.columns or "demand_quantity_kg" not in df_tgt.columns:
            continue

        sub = df_tgt[
            (df_tgt["district"].astype(str).str.strip().str.lower() == d_clean) &
            (df_tgt["crop"].astype(str).str.strip().str.lower() == c_clean)
        ].copy()

        if sub.empty:
            continue

        sub["date"] = pd.to_datetime(sub["date"], errors="coerce")
        sub["demand_quantity_kg"] = pd.to_numeric(sub["demand_quantity_kg"], errors="coerce")
        sub = sub.dropna(subset=["date", "demand_quantity_kg"]).sort_values("date").reset_index(drop=True)

        n_total = len(sub)
        min_train = 3
        if n_total < (min_train + 1):
            series_results.append({
                "district": tgt["district"],
                "crop": tgt["crop"],
                "status": "insufficient_history",
                "n_total": n_total,
                "mae": None,
                "rmse": None,
                "mape": None,
            })
            continue

        n_test = min(tgt.get("test_size", 2), n_total - min_train)
        n_train = n_total - n_test

        train_sub = sub.iloc[:n_train]
        test_sub = sub.iloc[n_train:]

        try:
            fc_res = forecast_demand(
                demand_df=train_sub,
                district=tgt["district"],
                crop=tgt["crop"],
                forecast_days=n_test,
            )
            if fc_res and "forecast_values" in fc_res:
                preds = np.asarray(fc_res["forecast_values"][:n_test], dtype=float)
                actuals = np.asarray(test_sub["demand_quantity_kg"].values, dtype=float)

                if len(preds) == len(actuals) and len(actuals) > 0:
                    errors = actuals - preds
                    mae = float(np.mean(np.abs(errors)))
                    rmse = float(np.sqrt(np.mean(errors ** 2)))
                    valid_m = np.abs(actuals) > 1e-6
                    mape = float(np.mean(np.abs(errors[valid_m] / actuals[valid_m])) * 100.0) if np.any(valid_m) else None

                    maes.append(mae)
                    rmses.append(rmse)
                    if mape is not None:
                        mapes.append(mape)

                    series_results.append({
                        "district": tgt["district"],
                        "crop": tgt["crop"],
                        "status": "success",
                        "n_total": n_total,
                        "n_train": n_train,
                        "n_test": n_test,
                        "mae": round(mae, 2),
                        "rmse": round(rmse, 2),
                        "mape": round(mape, 2) if mape is not None else None,
                    })
        except Exception:
            pass

    if not maes:
        return default_res

    avg_mae = round(float(np.mean(maes)), 2)
    avg_rmse = round(float(np.mean(rmses)), 2)
    avg_mape = round(float(np.mean(mapes)), 2) if mapes else None

    disp_parts = [f"MAE: {avg_mae:.1f} kg"]
    if avg_mape is not None:
        disp_parts.append(f"MAPE: {avg_mape:.1f}%")

    return {
        "series_evaluated": len(maes),
        "avg_mae": avg_mae,
        "avg_rmse": avg_rmse,
        "avg_mape": avg_mape,
        "display_text": ", ".join(disp_parts),
        "series_results": series_results,
    }


def calculate_quality_feedback_summary(
    feedback_df: Optional[pd.DataFrame] = None,
    produce_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """
    Summarizes quality assistance grades and feedback mentions.
    """
    if feedback_df is None:
        feedback_df = load_feedback()
    if produce_df is None:
        produce_df = load_produce()

    grade_counts = {}
    total_produce_lots = 0

    if produce_df is not None and isinstance(produce_df, pd.DataFrame) and not produce_df.empty:
        if "quality_grade" in produce_df.columns:
            grades = produce_df["quality_grade"].dropna().astype(str).str.strip().str.upper()
            total_produce_lots = len(grades)
            grade_counts = grades.value_counts().to_dict()

    quality_mentions = 0
    if feedback_df is not None and isinstance(feedback_df, pd.DataFrame) and not feedback_df.empty:
        if "comment" in feedback_df.columns:
            comments = feedback_df["comment"].dropna().astype(str).str.lower()
            quality_mentions = int(comments.str.contains("quality|grade|fresh|clean").sum())

    if total_produce_lots == 0 and quality_mentions == 0:
        return {
            "total_produce_lots": 0,
            "grade_distribution": {},
            "quality_feedback_mentions": 0,
            "display_text": "Insufficient data",
        }

    grade_summary_str = ", ".join([f"Grade {k}: {v}" for k, v in sorted(grade_counts.items())])
    return {
        "total_produce_lots": total_produce_lots,
        "grade_distribution": grade_counts,
        "quality_feedback_mentions": quality_mentions,
        "display_text": f"{grade_summary_str} ({quality_mentions} qualitative comments)",
    }


def calculate_learning_summary(
    transactions_df: Optional[pd.DataFrame] = None,
    feedback_df: Optional[pd.DataFrame] = None,
    produce_df: Optional[pd.DataFrame] = None,
    prices_df: Optional[pd.DataFrame] = None,
    demand_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    """
    Aggregates all performance, telemetry, and learning loop signals into a
    unified, governance-compliant learning summary.
    """
    if transactions_df is None:
        transactions_df = load_transactions()
    if feedback_df is None:
        feedback_df = load_feedback()
    if produce_df is None:
        produce_df = load_produce()
    if prices_df is None:
        prices_df = load_prices()
    if demand_df is None:
        demand_df = load_demand()

    tx_analyzed = len(transactions_df) if transactions_df is not None and isinstance(transactions_df, pd.DataFrame) else 0
    fb_count = len(feedback_df) if feedback_df is not None and isinstance(feedback_df, pd.DataFrame) else 0

    match_acc = calculate_match_acceptance(transactions_df)
    comp_rate = calculate_transaction_completion(transactions_df)
    fb_summary = calculate_feedback_summary(feedback_df)
    mkt_real = calculate_market_realization_comparison(transactions_df, produce_df, prices_df)
    fc_perf = calculate_forecast_performance(demand_df, transactions_df, produce_df)
    qual_fb = calculate_quality_feedback_summary(feedback_df, produce_df)

    has_data = (tx_analyzed > 0 or fb_count > 0)

    return {
        "status": "success" if has_data else "insufficient_data",
        "transactions_analyzed": tx_analyzed,
        "feedback_received": fb_count,
        "match_acceptance": match_acc,
        "completion_rate": comp_rate,
        "farmer_feedback": fb_summary["farmer"],
        "buyer_feedback": fb_summary["buyer"],
        "all_feedback": fb_summary["all_feedback"],
        "market_realization": mkt_real,
        "forecast_performance": fc_perf,
        "quality_feedback": qual_fb,
        "learning_note": LEARNING_NOTE,
        "model_retraining_governance": NO_RETRAIN_NOTE,
    }
