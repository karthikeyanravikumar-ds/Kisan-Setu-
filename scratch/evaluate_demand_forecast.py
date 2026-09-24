"""
Demand Forecast Evaluation Engine | Kisan Setu
Theme: 'Bharat, Reimagined'

Evaluates the existing demand forecasting model (ai/demand_forecasting.py)
using historical and transaction-derived demand data via chronological time-based splits.

Constraints & Principles:
- Strictly chronological time-based evaluation (no random shuffling / no data leakage).
- Evaluates:
    1. Pune + Onion (data/demand.csv)
    2. Pune + Tomato (data/demand.csv)
    3. Nashik + Onion (data/transactions.csv joined with data/produce.csv, labeled
       'Platform transaction-derived demand activity')
- Calculates MAE, RMSE, MAPE (with zero-division safety).
- Transparently reports sample sizes, train/test counts, and data limitations.
- Does not claim production-validation for small-sample prototype datasets.
"""

import sys
import os
import numpy as np
import pandas as pd

# Add repository root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from utils.data_loader import load_demand, load_transactions, load_produce
from utils.demand_data import build_transaction_demand_history
from ai.demand_forecasting import forecast_demand


def calculate_metrics(y_true, y_pred):
    """
    Computes MAE, RMSE, and MAPE with robust validation and zero-division protection.

    Parameters:
        y_true (list or np.ndarray): Ground truth actual values.
        y_pred (list or np.ndarray): Predicted values.

    Returns:
        dict: {'mae': float, 'rmse': float, 'mape': float or None}
    """
    if y_true is None or y_pred is None:
        return {"mae": None, "rmse": None, "mape": None}

    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)

    if len(y_t) == 0 or len(y_p) == 0 or len(y_t) != len(y_p):
        return {"mae": None, "rmse": None, "mape": None}

    errors = y_t - y_p
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors ** 2)))

    # Safe MAPE calculation ignoring zero or near-zero denominators
    valid_mask = np.abs(y_t) > 1e-6
    if np.any(valid_mask):
        mape = float(np.mean(np.abs(errors[valid_mask] / y_t[valid_mask])) * 100.0)
    else:
        mape = None

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": round(mape, 2) if mape is not None else None,
    }


def evaluate_demand_series(
    demand_df,
    district,
    crop,
    source_label="Historical demand dataset",
    min_train=3,
    test_size=None,
    train_ratio=0.67
):
    """
    Chronologically evaluates demand forecast for a single district + crop series.

    Parameters:
        demand_df (pd.DataFrame): Dataframe containing date, district, crop, demand_quantity_kg.
        district (str): Target district.
        crop (str): Target crop.
        source_label (str): Provenance description.
        min_train (int): Minimum required training observations (default 3).
        test_size (int, optional): Fixed number of test points. If None, derived from train_ratio.
        train_ratio (float): Ratio of series used for training when test_size is None.

    Returns:
        dict: Detailed evaluation results and telemetry.
    """
    if demand_df is None or not isinstance(demand_df, pd.DataFrame) or demand_df.empty:
        return {
            "status": "error",
            "message": "Input dataframe is empty or invalid.",
            "district": district,
            "crop": crop,
            "dataset_source": source_label,
            "n_total": 0,
            "n_train": 0,
            "n_test": 0,
            "mae": None,
            "rmse": None,
            "mape": None,
        }

    # Filter and clean series
    d_clean = str(district).strip().lower()
    c_clean = str(crop).strip().lower()

    filtered = demand_df[
        (demand_df["district"].astype(str).str.strip().str.lower() == d_clean) &
        (demand_df["crop"].astype(str).str.strip().str.lower() == c_clean)
    ].copy()

    if filtered.empty:
        return {
            "status": "no_data",
            "message": f"No records found for {district} - {crop}.",
            "district": district,
            "crop": crop,
            "dataset_source": source_label,
            "n_total": 0,
            "n_train": 0,
            "n_test": 0,
            "mae": None,
            "rmse": None,
            "mape": None,
        }

    # Parse and sort chronologically (No random shuffling)
    filtered["date"] = pd.to_datetime(filtered["date"], errors="coerce")
    filtered["demand_quantity_kg"] = pd.to_numeric(filtered["demand_quantity_kg"], errors="coerce")
    filtered = filtered.dropna(subset=["date", "demand_quantity_kg"])
    filtered = filtered.sort_values("date").reset_index(drop=True)

    n_total = len(filtered)

    # Need at least min_train + 1 records for an out-of-sample train/test split
    if n_total < (min_train + 1):
        return {
            "status": "insufficient_history",
            "message": (
                f"Sample has {n_total} observation(s). Model requires minimum {min_train} "
                f"training observations. At least {min_train + 1} observations are required for out-of-sample evaluation."
            ),
            "district": district,
            "crop": crop,
            "dataset_source": source_label,
            "n_total": n_total,
            "n_train": n_total if n_total >= min_train else 0,
            "n_test": 0,
            "train_dates": (filtered["date"].min().strftime("%Y-%m-%d"), filtered["date"].max().strftime("%Y-%m-%d")) if n_total > 0 else (None, None),
            "test_dates": (None, None),
            "actuals": [],
            "predictions": [],
            "mae": None,
            "rmse": None,
            "mape": None,
            "is_small_sample": True,
            "sample_note": "Sample size too small for out-of-sample evaluation.",
        }

    # Determine chronological split point
    if test_size is not None and test_size >= 1:
        n_train = max(min_train, n_total - int(test_size))
    else:
        n_train = max(min_train, int(np.floor(n_total * train_ratio)))
        if n_train >= n_total:
            n_train = n_total - 1

    n_test = n_total - n_train

    train_df = filtered.iloc[:n_train].copy()
    test_df = filtered.iloc[n_train:].copy()

    train_dates = (train_df["date"].min().strftime("%Y-%m-%d"), train_df["date"].max().strftime("%Y-%m-%d"))
    test_dates = (test_df["date"].min().strftime("%Y-%m-%d"), test_df["date"].max().strftime("%Y-%m-%d"))

    # Train model on historical training subset and forecast n_test steps ahead
    fc_result = forecast_demand(
        demand_df=train_df,
        district=district,
        crop=crop,
        forecast_days=n_test
    )

    if fc_result is None or "forecast_values" not in fc_result:
        return {
            "status": "forecast_failed",
            "message": "Forecast model could not generate predictions on training split.",
            "district": district,
            "crop": crop,
            "dataset_source": source_label,
            "n_total": n_total,
            "n_train": n_train,
            "n_test": n_test,
            "train_dates": train_dates,
            "test_dates": test_dates,
            "actuals": test_df["demand_quantity_kg"].tolist(),
            "predictions": [],
            "mae": None,
            "rmse": None,
            "mape": None,
        }

    preds = fc_result["forecast_values"][:n_test]
    actuals = test_df["demand_quantity_kg"].tolist()

    metrics = calculate_metrics(actuals, preds)

    return {
        "status": "success",
        "message": "Chronological evaluation completed.",
        "district": district,
        "crop": crop,
        "dataset_source": source_label,
        "n_total": n_total,
        "n_train": n_train,
        "n_test": n_test,
        "train_dates": train_dates,
        "test_dates": test_dates,
        "actuals": actuals,
        "predictions": preds,
        "mae": metrics["mae"],
        "rmse": metrics["rmse"],
        "mape": metrics["mape"],
        "is_small_sample": (n_total < 30),
        "sample_note": "Pilot/prototype dataset with small sample size. Directionally informative; not production-validated.",
    }


def run_full_evaluation():
    """
    Runs forecast evaluation across all standard benchmark series and prints
    a comprehensive, transparent performance report.
    """
    print("=" * 75)
    print("  KISAN SETU - DEMAND FORECASTING EVALUATION REPORT")
    print("  Evaluation Methodology: Strict Chronological Out-of-Sample Split")
    print("=" * 75)

    demand_df = load_demand()
    transactions_df = load_transactions()
    produce_df = load_produce()

    # 1. Platform Transaction-derived demand history
    tx_demand_df = build_transaction_demand_history(transactions_df, produce_df)

    evaluation_targets = [
        {
            "district": "Pune",
            "crop": "Onion",
            "df": demand_df,
            "source": "Historical demand dataset (data/demand.csv)",
            "test_size": 2,
        },
        {
            "district": "Pune",
            "crop": "Tomato",
            "df": demand_df,
            "source": "Historical demand dataset (data/demand.csv)",
            "test_size": 2,
        },
        {
            "district": "Nashik",
            "crop": "Onion",
            "df": tx_demand_df,
            "source": "Platform transaction-derived demand activity",
            "test_size": 1,
        },
    ]

    results = []

    for target in evaluation_targets:
        res = evaluate_demand_series(
            demand_df=target["df"],
            district=target["district"],
            crop=target["crop"],
            source_label=target["source"],
            test_size=target.get("test_size"),
        )
        results.append(res)

        print(f"\n--- [{res['district']} - {res['crop']}] ---")
        print(f"  Provenance:        {res['dataset_source']}")
        print(f"  Total Records:     {res['n_total']}")
        print(f"  Training Records:  {res['n_train']} {res.get('train_dates', '')}")
        print(f"  Test Records:      {res['n_test']} {res.get('test_dates', '')}")

        if res["status"] == "success":
            print(f"  Actuals:           {res['actuals']}")
            print(f"  Predictions:       {res['predictions']}")
            print(f"  MAE:               {res['mae']} kg")
            print(f"  RMSE:              {res['rmse']} kg")
            print(f"  MAPE:              {res['mape']}%")
            print(f"  Status:            {res['sample_note']}")
        elif res["status"] == "insufficient_history":
            print(f"  Status:            [!] {res['message']}")
            print(f"  MAE / RMSE / MAPE: N/A (Sample too small for out-of-sample split)")
        else:
            print(f"  Status:            [!] {res['message']}")

    print("\n" + "=" * 75)
    print("  SUMMARY OF LIMITATIONS & METHODOLOGY NOTES:")
    print("  1. Baseline Model: Ordinary Least Squares LinearRegression with order momentum.")
    print("  2. Small Sample Size: All series contain 3 to 6 historical daily observations.")
    print("  3. Out-of-sample validation on small sets illustrates directional tracking,")
    print("     but statistical confidence intervals require 30+ seasonal data points.")
    print("  4. Platform transaction activity represents recorded Kisan Setu orders,")
    print("     not total regional open market arrivals or wholesale volumes.")
    print("=" * 75)

    return results


if __name__ == "__main__":
    run_full_evaluation()
