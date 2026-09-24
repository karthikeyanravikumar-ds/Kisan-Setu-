"""
Payment & Settlement Simulation Engine | Kisan Setu
Theme: 'Bharat, Reimagined'

Simulates the financial transaction lifecycle for farmer and buyer settlement:
1. Gross Transaction Value Calculation
2. Logistics Freight Deduction
3. Platform Fee Computation (if configured)
4. Net Farmer Settlement Realization
5. Payment & Settlement Lifecycle State Transitions

GOVERNANCE & DISCLAIMER:
- PROTOTYPE ONLY: No real payment gateway integration and no real funds processed.
- Clearly labeled: "Prototype payment ledger — no real money is processed."
- Architecture: Keeps Estimated Net Realization and Actual Settlement as separate concepts.
"""

import os
import sys
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
PAYMENTS_CSV_PATH = ROOT_DIR / "data" / "payments.csv"

DISCLAIMER_TEXT = "Prototype payment ledger — no real money is processed."

# Valid Status Sets
VALID_PAYMENT_STATUSES = [
    "Payment Pending",
    "Payment Received",
    "Failed",
    "Refunded",
]

VALID_SETTLEMENT_STATUSES = [
    "Settlement Pending",
    "Settled",
    "Cancelled",
]

ALL_LIFECYCLE_STATUSES = [
    "Payment Pending",
    "Payment Received",
    "Settlement Pending",
    "Settled",
    "Failed",
    "Refunded",
    "Cancelled",
]

PAYMENT_COLUMNS = [
    "payment_id",
    "transaction_id",
    "buyer_id",
    "farmer_id",
    "gross_amount",
    "logistics_cost",
    "platform_fee",
    "net_settlement",
    "payment_status",
    "settlement_status",
    "payment_date",
    "settlement_date",
]


def load_payments(file_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """
    Loads payments records from data/payments.csv or custom path with fallback schema.
    """
    target = Path(file_path) if file_path else PAYMENTS_CSV_PATH
    if not target.exists():
        empty_df = pd.DataFrame(columns=PAYMENT_COLUMNS)
        for str_col in ["payment_id", "transaction_id", "buyer_id", "farmer_id", "payment_status", "settlement_status", "payment_date", "settlement_date"]:
            empty_df[str_col] = empty_df[str_col].astype(object)
        return empty_df

    try:
        df = pd.read_csv(target)
        # Ensure all columns exist
        for col in PAYMENT_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        # Ensure string columns are object dtype
        str_cols = ["payment_id", "transaction_id", "buyer_id", "farmer_id", "payment_status", "settlement_status", "payment_date", "settlement_date"]
        for scol in str_cols:
            df[scol] = df[scol].fillna("").astype(object)
        # Clean numeric fields
        for num_col in ["gross_amount", "logistics_cost", "platform_fee", "net_settlement"]:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce").fillna(0.0)
        return df
    except Exception:
        empty_df = pd.DataFrame(columns=PAYMENT_COLUMNS)
        for str_col in ["payment_id", "transaction_id", "buyer_id", "farmer_id", "payment_status", "settlement_status", "payment_date", "settlement_date"]:
            empty_df[str_col] = empty_df[str_col].astype(object)
        return empty_df


def save_payments(df: pd.DataFrame, file_path: Optional[Union[str, Path]] = None) -> bool:
    """
    Persists payment records to CSV.
    """
    target = Path(file_path) if file_path else PAYMENTS_CSV_PATH
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        df[PAYMENT_COLUMNS].to_csv(target, index=False)
        return True
    except Exception:
        return False


def calculate_settlement_breakdown(
    gross_amount: float,
    logistics_cost: float = 0.0,
    platform_fee: float = 0.0,
) -> Dict[str, Any]:
    """
    Calculates gross amount, deductions, and net settlement for farmer payout.
    
    Formula:
        net_settlement = gross_amount - logistics_cost - platform_fee
    
    Constraints:
        - All values must be non-negative numeric floats.
        - Keeps Actual Settlement distinct from Estimated Realization.
    """
    try:
        gross = max(0.0, float(gross_amount))
    except (ValueError, TypeError):
        gross = 0.0

    try:
        logistics = max(0.0, float(logistics_cost))
    except (ValueError, TypeError):
        logistics = 0.0

    try:
        fee = max(0.0, float(platform_fee))
    except (ValueError, TypeError):
        fee = 0.0

    net = round(gross - logistics - fee, 2)

    return {
        "gross_amount": round(gross, 2),
        "logistics_cost": round(logistics, 2),
        "platform_fee": round(fee, 2),
        "net_settlement": net,
        "disclaimer": DISCLAIMER_TEXT,
    }


def get_payment_for_transaction(
    transaction_id: str,
    payments_df: Optional[pd.DataFrame] = None,
    file_path: Optional[Union[str, Path]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Retrieves the payment record for a given transaction ID.
    """
    if not transaction_id:
        return None

    if payments_df is None:
        payments_df = load_payments(file_path)

    if payments_df.empty or "transaction_id" not in payments_df.columns:
        return None

    match = payments_df[payments_df["transaction_id"].astype(str) == str(transaction_id)]
    if match.empty:
        return None

    row = match.iloc[0]
    return {
        "payment_id": str(row.get("payment_id", "")),
        "transaction_id": str(row.get("transaction_id", "")),
        "buyer_id": str(row.get("buyer_id", "")),
        "farmer_id": str(row.get("farmer_id", "")),
        "gross_amount": float(row.get("gross_amount", 0.0)),
        "logistics_cost": float(row.get("logistics_cost", 0.0)),
        "platform_fee": float(row.get("platform_fee", 0.0)),
        "net_settlement": float(row.get("net_settlement", 0.0)),
        "payment_status": str(row.get("payment_status", "Payment Pending")),
        "settlement_status": str(row.get("settlement_status", "Settlement Pending")),
        "payment_date": str(row.get("payment_date", "")),
        "settlement_date": str(row.get("settlement_date", "")),
        "disclaimer": DISCLAIMER_TEXT,
    }


def record_or_update_payment(
    transaction_id: str,
    buyer_id: str,
    farmer_id: str,
    gross_amount: float,
    logistics_cost: float = 0.0,
    platform_fee: float = 0.0,
    payment_status: str = "Payment Pending",
    settlement_status: str = "Settlement Pending",
    payment_date: Optional[str] = None,
    settlement_date: Optional[str] = None,
    file_path: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """
    Creates or updates a payment & settlement record.
    """
    df = load_payments(file_path)
    breakdown = calculate_settlement_breakdown(gross_amount, logistics_cost, platform_fee)

    # Validate statuses
    p_stat = payment_status if payment_status in VALID_PAYMENT_STATUSES else "Payment Pending"
    s_stat = settlement_status if settlement_status in VALID_SETTLEMENT_STATUSES else "Settlement Pending"

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    p_date = payment_date if payment_date is not None else (today_str if p_stat == "Payment Received" else "")
    s_date = settlement_date if settlement_date is not None else (today_str if s_stat == "Settled" else "")

    existing_idx = df[df["transaction_id"].astype(str) == str(transaction_id)].index if not df.empty else []

    if len(existing_idx) > 0:
        idx = existing_idx[0]
        pay_id = str(df.at[idx, "payment_id"])
        df.at[idx, "buyer_id"] = str(buyer_id)
        df.at[idx, "farmer_id"] = str(farmer_id)
        df.at[idx, "gross_amount"] = breakdown["gross_amount"]
        df.at[idx, "logistics_cost"] = breakdown["logistics_cost"]
        df.at[idx, "platform_fee"] = breakdown["platform_fee"]
        df.at[idx, "net_settlement"] = breakdown["net_settlement"]
        df.at[idx, "payment_status"] = p_stat
        df.at[idx, "settlement_status"] = s_stat
        if p_date:
            df.at[idx, "payment_date"] = p_date
        if s_date:
            df.at[idx, "settlement_date"] = s_date
    else:
        # Generate new payment_id
        if not df.empty and "payment_id" in df.columns:
            nums = (
                df["payment_id"]
                .astype(str)
                .str.extract(r"PAY(\d+)", expand=False)
                .dropna()
                .astype(int)
            )
            next_num = int(nums.max() + 1) if not nums.empty else 1
        else:
            next_num = 1
        pay_id = f"PAY{next_num:03d}"

        new_row = {
            "payment_id": pay_id,
            "transaction_id": str(transaction_id),
            "buyer_id": str(buyer_id),
            "farmer_id": str(farmer_id),
            "gross_amount": breakdown["gross_amount"],
            "logistics_cost": breakdown["logistics_cost"],
            "platform_fee": breakdown["platform_fee"],
            "net_settlement": breakdown["net_settlement"],
            "payment_status": p_stat,
            "settlement_status": s_stat,
            "payment_date": p_date or "",
            "settlement_date": s_date or "",
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    save_payments(df, file_path)

    return {
        "payment_id": pay_id,
        "transaction_id": str(transaction_id),
        "buyer_id": str(buyer_id),
        "farmer_id": str(farmer_id),
        "gross_amount": breakdown["gross_amount"],
        "logistics_cost": breakdown["logistics_cost"],
        "platform_fee": breakdown["platform_fee"],
        "net_settlement": breakdown["net_settlement"],
        "payment_status": p_stat,
        "settlement_status": s_stat,
        "payment_date": p_date,
        "settlement_date": s_date,
        "disclaimer": DISCLAIMER_TEXT,
    }


def update_payment_status(
    transaction_id: str,
    new_status: str,
    payment_date: Optional[str] = None,
    file_path: Optional[Union[str, Path]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Updates the payment status of a transaction (e.g., Payment Received, Failed, Refunded).
    """
    if not transaction_id or new_status not in VALID_PAYMENT_STATUSES:
        return None

    df = load_payments(file_path)
    if df.empty or "transaction_id" not in df.columns:
        return None

    idx_list = df[df["transaction_id"].astype(str) == str(transaction_id)].index
    if len(idx_list) == 0:
        return None

    idx = idx_list[0]
    df.at[idx, "payment_status"] = new_status
    if new_status == "Payment Received":
        df.at[idx, "payment_date"] = payment_date or datetime.date.today().strftime("%Y-%m-%d")

    save_payments(df, file_path)
    return get_payment_for_transaction(transaction_id, df)


def update_settlement_status(
    transaction_id: str,
    new_status: str,
    settlement_date: Optional[str] = None,
    file_path: Optional[Union[str, Path]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Updates the settlement status of a transaction (e.g., Settled, Cancelled).
    """
    if not transaction_id or new_status not in VALID_SETTLEMENT_STATUSES:
        return None

    df = load_payments(file_path)
    if df.empty or "transaction_id" not in df.columns:
        return None

    idx_list = df[df["transaction_id"].astype(str) == str(transaction_id)].index
    if len(idx_list) == 0:
        return None

    idx = idx_list[0]
    df.at[idx, "settlement_status"] = new_status
    if new_status == "Settled":
        df.at[idx, "settlement_date"] = settlement_date or datetime.date.today().strftime("%Y-%m-%d")

    save_payments(df, file_path)
    return get_payment_for_transaction(transaction_id, df)
