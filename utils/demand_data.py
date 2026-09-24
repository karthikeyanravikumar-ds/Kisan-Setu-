"""
Kisan Setu Demand Data Preparation Engine
Derives platform realized/committed demand history from verified transactions.
Theme: 'Bharat, Reimagined'
"""
import pandas as pd
import numpy as np


VALID_DEMAND_STATUSES = {
    "order placed",
    "confirmed",
    "in transit",
    "completed",
    "delivered",
}


def build_transaction_demand_history(
    transactions_df,
    produce_df,
    valid_statuses=None
):
    """
    Derives platform demand history by joining transactions with produce metadata.
    
    This represents PLATFORM REALIZED/COMMITTED DEMAND ACTIVITY on Kisan Setu,
    and should not be claimed as total open-market demand without qualification.

    Parameters:
        transactions_df (pd.DataFrame): Raw transactions dataset.
        produce_df (pd.DataFrame): Produce lots dataset with crop and district mappings.
        valid_statuses (set or list, optional): Custom status whitelist for valid commitments.

    Returns:
        pd.DataFrame: Cleaned aggregated demand dataframe with columns:
                      ['date', 'district', 'crop', 'demand_quantity_kg', 'orders']
    """
    empty_result = pd.DataFrame(columns=["date", "district", "crop", "demand_quantity_kg", "orders"])

    if transactions_df is None or produce_df is None:
        return empty_result

    if not isinstance(transactions_df, pd.DataFrame) or not isinstance(produce_df, pd.DataFrame):
        return empty_result

    if transactions_df.empty or produce_df.empty:
        return empty_result

    # 1. Validate required transaction columns
    tx_required = {"transaction_id", "produce_id", "quantity_kg", "date"}
    if not tx_required.issubset(set(transactions_df.columns)):
        return empty_result

    # 2. Validate required produce columns
    prod_required = {"produce_id", "crop", "district"}
    if not prod_required.issubset(set(produce_df.columns)):
        return empty_result

    # 3. Status handling & Deduplication of transaction_id
    if valid_statuses is not None:
        allowed_statuses = set(str(s).strip().lower() for s in valid_statuses)
    else:
        allowed_statuses = VALID_DEMAND_STATUSES

    tx_clean = transactions_df.copy()
    tx_clean = tx_clean.dropna(subset=["transaction_id"]).drop_duplicates(subset=["transaction_id"], keep="first")

    if "status" in tx_clean.columns:
        status_mask = tx_clean["status"].astype(str).str.strip().str.lower().isin(allowed_statuses)
        tx_clean = tx_clean[status_mask]

    if tx_clean.empty:
        return empty_result

    # 4. Clean produce records
    prod_clean = produce_df.dropna(subset=["produce_id", "crop", "district"]).copy()
    prod_clean["produce_id_clean"] = prod_clean["produce_id"].astype(str).str.strip().str.upper()
    prod_clean["crop_clean"] = prod_clean["crop"].astype(str).str.strip().str.title()
    prod_clean["district_clean"] = prod_clean["district"].astype(str).str.strip().str.title()
    prod_clean = prod_clean.drop_duplicates(subset=["produce_id_clean"], keep="first")

    # 5. Join transactions with produce
    tx_clean["produce_id_clean"] = tx_clean["produce_id"].astype(str).str.strip().str.upper()
    merged = pd.merge(
        tx_clean,
        prod_clean[["produce_id_clean", "crop_clean", "district_clean"]],
        on="produce_id_clean",
        how="inner"
    )

    if merged.empty:
        return empty_result

    # 6. Parse and validate dates
    merged["date_dt"] = pd.to_datetime(merged["date"], errors="coerce")
    merged = merged.dropna(subset=["date_dt"])

    # 7. Convert quantity_kg to numeric and filter strictly positive values
    merged["quantity_kg_num"] = pd.to_numeric(merged["quantity_kg"], errors="coerce")
    merged = merged.dropna(subset=["quantity_kg_num"])
    merged = merged[merged["quantity_kg_num"] > 0]

    if merged.empty:
        return empty_result

    # Format standard date string YYYY-MM-DD
    merged["date_str"] = merged["date_dt"].dt.strftime("%Y-%m-%d")

    # 8. Aggregate by date, district, crop using SUM(quantity_kg) and COUNT(transaction_id)
    aggregated = merged.groupby(
        ["date_str", "district_clean", "crop_clean"],
        as_index=False
    ).agg(
        demand_quantity_kg=("quantity_kg_num", "sum"),
        orders=("transaction_id", "count")
    )

    aggregated = aggregated.rename(columns={
        "date_str": "date",
        "district_clean": "district",
        "crop_clean": "crop"
    })

    aggregated = aggregated.sort_values(["district", "crop", "date"]).reset_index(drop=True)
    return aggregated[["date", "district", "crop", "demand_quantity_kg", "orders"]]


def get_regional_demand_series(
    district,
    crop,
    demand_df,
    transactions_df=None,
    produce_df=None
):
    """
    Resolves the appropriate demand dataset for a given district and crop
    using a strict hierarchical lookup without mixing disparate data sources.

    Hierarchy:
    1. Historical demand dataset (data/demand.csv) if >= 3 observations exist.
    2. Platform transaction-derived demand history if >= 3 observations exist.
    3. None / Empty (forecast unavailable).

    Returns:
        tuple (pd.DataFrame or None, str): (resolved_demand_df, demand_source_label)
    """
    if not district or not crop:
        return None, "Unavailable"

    target_district = str(district).strip().lower()
    target_crop = str(crop).strip().lower()

    # 1. Check primary historical demand dataset
    if demand_df is not None and isinstance(demand_df, pd.DataFrame) and not demand_df.empty:
        req_cols = {"date", "district", "crop", "demand_quantity_kg"}
        if req_cols.issubset(set(demand_df.columns)):
            d_mask = demand_df["district"].astype(str).str.strip().str.lower() == target_district
            c_mask = demand_df["crop"].astype(str).str.strip().str.lower() == target_crop
            hist_match = demand_df[d_mask & c_mask]
            if len(hist_match) >= 3:
                return demand_df, "Historical demand dataset"

    # 2. Check platform transaction-derived demand history
    if transactions_df is not None and produce_df is not None:
        tx_demand_df = build_transaction_demand_history(transactions_df, produce_df)
        if not tx_demand_df.empty:
            d_mask = tx_demand_df["district"].astype(str).str.strip().str.lower() == target_district
            c_mask = tx_demand_df["crop"].astype(str).str.strip().str.lower() == target_crop
            tx_match = tx_demand_df[d_mask & c_mask]
            if len(tx_match) >= 3:
                return tx_demand_df, "Platform transaction history"

    return None, "Unavailable"
