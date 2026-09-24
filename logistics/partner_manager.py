"""
Logistics Partner Management & Prototype Orchestration Engine | Kisan Setu
Theme: 'Bharat, Reimagined'

Manages prototype logistics partner network for agricultural load fulfillment:
1. Loads available regional logistics partners.
2. Matches delivery requirements using load weight, vehicle capacity, origin/destination service area, and availability.
3. Computes transparent freight rates using existing distance algorithms.
4. Orchestrates partner assignments and lifecycle status transitions.

IMPORTANT:
This is a prototype logistics partner network layer.
Partners and assignments represent simulated dispatch operations on Kisan Setu.
"""

import os
from datetime import datetime, date
import pandas as pd
import numpy as np

from ai.matching import get_distance

VALID_PARTNER_STATUSES = [
    "Requested",
    "Assigned",
    "Pickup Scheduled",
    "In Transit",
    "Delivered",
    "Cancelled",
]

PROTOTYPE_NETWORK_LABEL = "Prototype logistics partner network"
NO_THIRD_PARTY_NOTE = "No real third-party logistics provider is connected."
EXPLANATORY_NOTE = (
    "Kisan Setu connects the trade decision with fulfilment by matching each transaction "
    "with an eligible logistics partner based on capacity, service area, availability and estimated freight."
)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

DEFAULT_PARTNERS_FILE = os.path.join(DATA_DIR, "logistics_partners.csv")

LOGISTICS_ASSIGNMENTS_FILE = os.path.join(DATA_DIR, "logistics_assignments.csv")
PARTNER_ASSIGNMENTS_FILE = os.path.join(DATA_DIR, "partner_assignments.csv")

# Use logistics_assignments.csv as primary
DEFAULT_ASSIGNMENTS_FILE = LOGISTICS_ASSIGNMENTS_FILE if os.path.exists(LOGISTICS_ASSIGNMENTS_FILE) else PARTNER_ASSIGNMENTS_FILE


def load_logistics_partners(filepath=None):
    """
    Loads all registered logistics partners from CSV.

    Parameters:
        filepath (str, optional): Custom path to logistics_partners.csv.

    Returns:
        pd.DataFrame: DataFrame of logistics partners.
    """
    path = filepath or DEFAULT_PARTNERS_FILE
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            # Ensure numeric types
            if "capacity_kg" in df.columns:
                df["capacity_kg"] = pd.to_numeric(df["capacity_kg"], errors="coerce").fillna(1000)
            if "cost_per_km" in df.columns:
                df["cost_per_km"] = pd.to_numeric(df["cost_per_km"], errors="coerce").fillna(30.0)
            if "base_cost" in df.columns:
                df["base_cost"] = pd.to_numeric(df["base_cost"], errors="coerce").fillna(500.0)
            return df
        except Exception:
            pass

    # Fallback prototype partners if file unreadable
    fallback_data = [
        {"partner_id": "LP001", "partner_name": "Sahyadri Agro Transporters", "vehicle_type": "Mini Truck", "capacity_kg": 1200, "base_location": "Nashik", "service_regions": "Nashik, Pune, Ahmednagar, Mumbai", "cost_per_km": 28.0, "base_cost": 500.0, "availability": "Available", "rating": 4.8, "contact_phone": "+91 98220 44101"},
        {"partner_id": "LP002", "partner_name": "Godavari Express Logistics", "vehicle_type": "Medium Eicher", "capacity_kg": 2500, "base_location": "Nashik", "service_regions": "Nashik, Pune, Mumbai, Thane", "cost_per_km": 35.0, "base_cost": 800.0, "availability": "Available", "rating": 4.7, "contact_phone": "+91 98220 44102"},
        {"partner_id": "LP003", "partner_name": "Deccan Rural Haulage", "vehicle_type": "Pickup 4x4", "capacity_kg": 600, "base_location": "Ahmednagar", "service_regions": "Ahmednagar, Pune, Nashik", "cost_per_km": 22.0, "base_cost": 350.0, "availability": "Available", "rating": 4.9, "contact_phone": "+91 98220 44103"},
        {"partner_id": "LP004", "partner_name": "Kisan Setu Fleet Unit 1", "vehicle_type": "Refrigerated Van", "capacity_kg": 1500, "base_location": "Pune", "service_regions": "Pune, Mumbai, Nashik, Satara", "cost_per_km": 38.0, "base_cost": 900.0, "availability": "Busy", "rating": 4.6, "contact_phone": "+91 98220 44104"},
        {"partner_id": "LP005", "partner_name": "Western Ghats Freight", "vehicle_type": "Heavy Carrier", "capacity_kg": 5000, "base_location": "Pune", "service_regions": "Pune, Mumbai, Nashik, Ahmednagar", "cost_per_km": 52.0, "base_cost": 1500.0, "availability": "Available", "rating": 4.5, "contact_phone": "+91 98220 44105"},
    ]
    return pd.DataFrame(fallback_data)


def match_logistics_partners(
    required_quantity_kg,
    origin,
    destination,
    only_available=True,
    max_results=5,
    partners_df=None,
    partners_file=None,
):
    """
    Finds and ranks suitable logistics partners based on capacity, service area, and freight rate.

    Parameters:
        required_quantity_kg (float): Weight of the shipment load in kg.
        origin (str): Origin location or district (e.g. 'Niphad', 'Nashik').
        destination (str): Destination location or district (e.g. 'Pune', 'Mumbai').
        only_available (bool): If True, only matches partners with status 'Available'.
        max_results (int): Maximum number of top matching partners to return.
        partners_df (pd.DataFrame, optional): Pre-loaded partners DataFrame.
        partners_file (str, optional): Custom path to partners CSV.

    Returns:
        list[dict]: Ranked list of matching logistics partners with telemetry and freight costs.
    """
    df = partners_df if partners_df is not None else load_logistics_partners(partners_file)
    if df.empty:
        return []

    try:
        req_qty = float(required_quantity_kg)
        if req_qty <= 0:
            req_qty = 100.0
    except (ValueError, TypeError):
        req_qty = 100.0

    # Extract district tokens for distance lookup
    def extract_district(loc_str):
        if not loc_str or not isinstance(loc_str, str):
            return "Nashik"
        parts = [p.strip().title() for p in loc_str.split(",")]
        # Known major hubs
        for part in reversed(parts):
            if part in ["Nashik", "Pune", "Ahmednagar", "Mumbai", "Thane", "Satara", "Nagpur"]:
                return part
        return parts[-1] if parts else "Nashik"

    origin_dist = extract_district(origin)
    dest_dist = extract_district(destination)

    distance_km = float(get_distance(origin_dist, dest_dist))

    matches = []
    for _, row in df.iterrows():
        p_id = str(row["partner_id"])
        p_name = str(row["partner_name"])
        v_type = str(row["vehicle_type"])
        capacity = float(row.get("capacity_kg", 1000))
        cost_km = float(row.get("cost_per_km", 30.0))
        base_c = float(row.get("base_cost", 500.0))
        availability = str(row.get("availability", "Available"))
        rating = float(row.get("rating", 4.5))
        base_loc = str(row.get("base_location", "Nashik"))
        service_regions = str(row.get("service_regions", "Nashik, Pune, Ahmednagar, Mumbai"))
        phone = str(row.get("contact_phone", "+91 98220 00000"))

        # 1. Availability filter
        if only_available and availability.strip().lower() != "available":
            continue

        # 2. Capacity filter (vehicle must be capable of carrying the load)
        if capacity < req_qty:
            continue

        # 3. Service region check (origin or destination within service network)
        regions_list = [r.strip().lower() for r in service_regions.split(",")]
        origin_match = (origin_dist.lower() in regions_list) or (base_loc.lower() == origin_dist.lower())
        dest_match = (dest_dist.lower() in regions_list) or (base_loc.lower() == dest_dist.lower())
        
        # If neither matches and specific regions are configured, skip
        if not (origin_match or dest_match) and len(regions_list) > 1:
            continue

        # 4. Freight Calculation
        estimated_freight = round(base_c + (distance_km * cost_km), 2)
        freight_per_kg = round(estimated_freight / req_qty, 2) if req_qty > 0 else 0.0
        utilization_pct = min(100.0, round((req_qty / capacity) * 100.0, 1))

        # 5. Composite Suitability Score (0-100)
        # Optimal utilization (70-90%) scores highest, plus rating boost, lower cost per km
        util_score = 100 - abs(utilization_pct - 80)
        cost_score = max(20.0, 100.0 - (cost_km * 1.5))
        rating_score = (rating / 5.0) * 100.0
        suitability_score = round(0.40 * util_score + 0.35 * cost_score + 0.25 * rating_score, 1)

        matches.append({
            "partner_id": p_id,
            "partner_name": p_name,
            "vehicle_type": v_type,
            "capacity_kg": capacity,
            "required_quantity_kg": req_qty,
            "capacity_utilization_pct": utilization_pct,
            "base_location": base_loc,
            "service_regions": service_regions,
            "distance_km": distance_km,
            "cost_per_km": cost_km,
            "base_cost": base_c,
            "estimated_freight": estimated_freight,
            "freight_per_kg": freight_per_kg,
            "availability": availability,
            "rating": rating,
            "contact_phone": phone,
            "suitability_score": suitability_score,
            "origin": origin,
            "destination": destination,
            "network_type": "Prototype logistics partner network",
        })

    # Sort by suitability score descending
    matches.sort(key=lambda x: x["suitability_score"], reverse=True)
    return matches[:max_results]


def load_partner_assignments(assignments_file=None):
    """
    Loads all partner transaction assignments from CSV.
    """
    path = assignments_file or DEFAULT_ASSIGNMENTS_FILE
    if os.path.exists(path):
        try:
            return pd.read_csv(path)
        except Exception:
            pass

    return pd.DataFrame(columns=[
        "assignment_id",
        "partner_id",
        "transaction_id",
        "vehicle",
        "pickup_location",
        "destination",
        "quantity_kg",
        "estimated_freight",
        "status",
        "created_at",
        "updated_at",
    ])


def assign_partner_to_transaction(
    partner_id,
    transaction_id,
    pickup_location,
    destination,
    quantity_kg=500.0,
    estimated_freight=None,
    vehicle=None,
    status="Assigned",
    assignments_file=None,
    partners_file=None,
):
    """
    Assigns a logistics partner to a specific transaction and records it.

    Parameters:
        partner_id (str): Partner ID (e.g. 'LP001').
        transaction_id (str): Transaction ID (e.g. 'T001').
        pickup_location (str): Farm gate origin.
        destination (str): Delivery hub / buyer destination.
        quantity_kg (float): Weight of the load.
        estimated_freight (float, optional): Calculated freight cost.
        vehicle (str, optional): Vehicle type description.
        status (str): Initial assignment status (default 'Assigned').
        assignments_file (str, optional): Custom path to assignments CSV.
        partners_file (str, optional): Custom path to partners CSV.

    Returns:
        dict: Created assignment record.
    """
    assignments_df = load_partner_assignments(assignments_file)

    # Validate status
    if status not in VALID_PARTNER_STATUSES:
        status = "Assigned"

    # Resolve partner metadata if vehicle/freight missing
    if not vehicle or estimated_freight is None:
        partners_df = load_logistics_partners(partners_file)
        p_row = partners_df[partners_df["partner_id"].astype(str) == str(partner_id)]
        if not p_row.empty:
            p_info = p_row.iloc[0]
            if not vehicle:
                vehicle = str(p_info.get("vehicle_type", "Mini Truck"))
            if estimated_freight is None:
                cost_km = float(p_info.get("cost_per_km", 28.0))
                base_c = float(p_info.get("base_cost", 500.0))
                dist = float(get_distance("Nashik", "Pune"))
                estimated_freight = round(base_c + (dist * cost_km), 2)
        else:
            vehicle = vehicle or "Mini Truck"
            estimated_freight = estimated_freight or 1500.0

    today_str = date.today().strftime("%Y-%m-%d")

    # Generate next assignment ID
    if not assignments_df.empty and "assignment_id" in assignments_df.columns:
        last_id = str(assignments_df["assignment_id"].iloc[-1])
        try:
            next_num = int(last_id.replace("PA", "")) + 1
            new_assign_id = f"PA{next_num:03d}"
        except Exception:
            new_assign_id = f"PA{len(assignments_df) + 1:03d}"
    else:
        new_assign_id = "PA001"

    # Derive distance if possible
    try:
        orig_token = str(pickup_location).split(",")[-1].strip()
        dest_token = str(destination).split(",")[-1].strip()
        calc_dist = float(get_distance(orig_token, dest_token))
    except Exception:
        calc_dist = 150.0

    new_record = {
        "assignment_id": new_assign_id,
        "partner_id": str(partner_id),
        "transaction_id": str(transaction_id),
        "vehicle_type": str(vehicle),
        "vehicle": str(vehicle),
        "pickup_location": str(pickup_location),
        "destination": str(destination),
        "quantity_kg": float(quantity_kg),
        "distance_km": float(calc_dist),
        "estimated_freight": float(estimated_freight),
        "status": str(status),
        "assigned_at": today_str,
        "pickup_date": today_str,
        "created_at": today_str,
        "updated_at": today_str,
    }

    # If transaction already assigned, update existing record
    tx_match = assignments_df[assignments_df["transaction_id"].astype(str) == str(transaction_id)] if not assignments_df.empty else pd.DataFrame()
    if not tx_match.empty:
        idx = tx_match.index[-1]
        for k, v in new_record.items():
            if k not in ["assignment_id", "created_at", "assigned_at"]:
                assignments_df.at[idx, k] = v
        new_record["assignment_id"] = str(assignments_df.at[idx, "assignment_id"])
    else:
        new_row_df = pd.DataFrame([new_record])
        assignments_df = pd.concat([assignments_df, new_row_df], ignore_index=True)

    # Save to primary assignments file
    save_path = assignments_file or DEFAULT_ASSIGNMENTS_FILE
    try:
        assignments_df.to_csv(save_path, index=False)
        # Also mirror to partner_assignments.csv / logistics_assignments.csv if distinct
        if save_path == LOGISTICS_ASSIGNMENTS_FILE and os.path.exists(PARTNER_ASSIGNMENTS_FILE):
            assignments_df.to_csv(PARTNER_ASSIGNMENTS_FILE, index=False)
        elif save_path == PARTNER_ASSIGNMENTS_FILE and os.path.exists(LOGISTICS_ASSIGNMENTS_FILE):
            assignments_df.to_csv(LOGISTICS_ASSIGNMENTS_FILE, index=False)
    except Exception:
        pass

    return new_record


def update_partner_assignment_status(
    transaction_id_or_assignment_id,
    new_status,
    assignments_file=None
):
    """
    Updates the lifecycle status of a logistics partner assignment.

    Parameters:
        transaction_id_or_assignment_id (str): Transaction ID (e.g. 'T001') or Assignment ID ('PA001').
        new_status (str): One of VALID_PARTNER_STATUSES.
        assignments_file (str, optional): Custom path to assignments CSV.

    Returns:
        dict or None: Updated assignment record or None if not found/invalid.
    """
    if new_status not in VALID_PARTNER_STATUSES:
        return None

    assignments_df = load_partner_assignments(assignments_file)
    if assignments_df.empty:
        return None

    key_str = str(transaction_id_or_assignment_id).strip()
    match_mask = (
        (assignments_df["transaction_id"].astype(str).str.strip() == key_str) |
        (assignments_df["assignment_id"].astype(str).str.strip() == key_str)
    )

    if not match_mask.any():
        return None

    idx = assignments_df[match_mask].index[-1]
    today_str = date.today().strftime("%Y-%m-%d")

    assignments_df.at[idx, "status"] = new_status
    assignments_df.at[idx, "updated_at"] = today_str

    save_path = assignments_file or DEFAULT_ASSIGNMENTS_FILE
    try:
        assignments_df.to_csv(save_path, index=False)
        if save_path == LOGISTICS_ASSIGNMENTS_FILE and os.path.exists(PARTNER_ASSIGNMENTS_FILE):
            assignments_df.to_csv(PARTNER_ASSIGNMENTS_FILE, index=False)
        elif save_path == PARTNER_ASSIGNMENTS_FILE and os.path.exists(LOGISTICS_ASSIGNMENTS_FILE):
            assignments_df.to_csv(LOGISTICS_ASSIGNMENTS_FILE, index=False)
    except Exception:
        pass

    return assignments_df.iloc[idx].to_dict()


def get_partner_for_transaction(transaction_id, assignments_file=None, partners_file=None):
    """
    Retrieves assigned logistics partner metadata for a given transaction ID.

    Returns:
        dict or None: Full partner assignment details or None if unassigned.
    """
    assignments_df = load_partner_assignments(assignments_file)
    if assignments_df.empty:
        return None

    match = assignments_df[assignments_df["transaction_id"].astype(str) == str(transaction_id)]
    if match.empty:
        return None

    assign_row = match.iloc[-1].to_dict()
    partners_df = load_logistics_partners(partners_file)
    p_row = partners_df[partners_df["partner_id"].astype(str) == str(assign_row["partner_id"])]

    if not p_row.empty:
        p_info = p_row.iloc[0].to_dict()
        assign_row["partner_name"] = p_info.get("partner_name", "Partner Fleet")
        assign_row["contact_phone"] = p_info.get("contact_phone", "")
        assign_row["rating"] = p_info.get("rating", 4.8)
    else:
        assign_row["partner_name"] = f"Partner {assign_row['partner_id']}"
        assign_row["contact_phone"] = ""
        assign_row["rating"] = 4.8

    assign_row["network_type"] = PROTOTYPE_NETWORK_LABEL
    return assign_row


def render_logistics_status_stepper_html(current_status: str) -> str:
    """
    Renders an editorial visual status tracker stepper for the logistics fulfillment flow:
    Requested -> Assigned -> Pickup Scheduled -> In Transit -> Delivered (or Cancelled)
    """
    stages = [
        ("Requested", "📋"),
        ("Assigned", "🤝"),
        ("Pickup Scheduled", "📦"),
        ("In Transit", "🚚"),
        ("Delivered", "✅"),
    ]

    status_clean = str(current_status).strip()
    is_cancelled = (status_clean.lower() in ["cancelled", "failed", "rejected"])
    status_order = {s[0]: i for i, s in enumerate(stages)}
    curr_idx = -1 if is_cancelled else status_order.get(status_clean, -1)

    steps_html = []
    for i, (stage_name, stage_icon) in enumerate(stages):
        if is_cancelled:
            dot_color = "#9E4932"
            bg_color = "#FDF4F2"
            border_color = "#EAB5A8"
            font_weight = "500"
            state_label = "✕"
            tag_text = "CANCELLED"
            font_color = "#9E4932"
            sub_color = "#9E4932"
        elif curr_idx >= 0 and i < curr_idx:
            # Completed stage
            dot_color = "#176536"
            bg_color = "rgba(23, 101, 54, 0.12)"
            border_color = "#176536"
            font_weight = "700"
            state_label = "✓"
            tag_text = "DONE"
            font_color = "#18201B"
            sub_color = "#176536"
        elif curr_idx >= 0 and i == curr_idx:
            # Active current stage
            dot_color = "#FFFFFF"
            bg_color = "#163E2B"
            border_color = "#E5A010"
            font_weight = "900"
            state_label = "●"
            tag_text = "ACTIVE"
            font_color = "#FFFFFF"
            sub_color = "#F59E0B"
        else:
            # Upcoming stage
            dot_color = "#A3ACA6"
            bg_color = "#F5F3ED"
            border_color = "#D4CEC3"
            font_weight = "500"
            state_label = "○"
            tag_text = "PENDING"
            font_color = "#18201B"
            sub_color = "#68756C"

        step_card = f"""
        <div style="flex: 1; min-width: 105px; background: {bg_color}; border: 1.5px solid {border_color}; border-radius: 8px; padding: 8px 10px; text-align: center; margin: 3px;">
            <div style="font-size: 0.95rem;">{stage_icon}</div>
            <div style="font-size: 0.76rem; font-weight: {font_weight}; color: {font_color}; margin-top: 2px;">
                {stage_name}
            </div>
            <div style="font-size: 0.68rem; color: {sub_color}; font-weight: 700;">
                {state_label} {tag_text}
            </div>
        </div>
        """
        steps_html.append(step_card)

    cancel_banner = f"""
    <div style="background: #FDF4F2; border: 1px solid #EAB5A8; color: #9E4932; border-radius: 6px; padding: 6px 12px; font-size: 0.82rem; font-weight: 700; margin-top: 8px; text-align: center;">
        🚫 Shipment Status: Cancelled
    </div>
    """ if is_cancelled else ""

    return f"""
    <div style="background: #FFFFFF; border: 1px solid #E5DFD3; border-radius: 12px; padding: 14px; margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 6px;">
            <span style="font-weight: 800; font-size: 0.85rem; color: #163E2B;">🚚 LOGISTICS STATUS TRACKER</span>
            <span style="font-size: 0.74rem; background: rgba(22,62,43,0.08); color: #163E2B; padding: 2px 8px; border-radius: 6px; font-weight: 700;">{PROTOTYPE_NETWORK_LABEL}</span>
        </div>
        <div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between;">
            {''.join(steps_html)}
        </div>
        {cancel_banner}
    </div>
    """

