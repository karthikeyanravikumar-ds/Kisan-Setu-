import pandas as pd
from pathlib import Path
from datetime import datetime

from utils.data_loader import (
    load_farmers,
    load_produce,
    load_prices,
    load_demand,
    load_buyers
)

from ai.matching import find_matches
from ai.demand_forecasting import forecast_demand


DATA_DIR = Path(__file__).resolve().parent.parent / "data"

SMS_FILE = DATA_DIR / "sms_messages.csv"

SMS_COLUMNS = [
    "message_id",
    "phone",
    "farmer_id",
    "direction",
    "message",
    "response",
    "timestamp"
]


# =========================================================
# SMS STORAGE
# =========================================================

def load_sms_messages():

    if not SMS_FILE.exists():

        return pd.DataFrame(
            columns=SMS_COLUMNS
        )

    df = pd.read_csv(SMS_FILE)

    for column in SMS_COLUMNS:

        if column not in df.columns:
            df[column] = None

    return df[SMS_COLUMNS]


def generate_message_id(df):

    if df.empty:
        return "SMS001"

    numbers = []

    for message_id in df["message_id"].astype(str):

        try:

            number = int(
                message_id.replace("SMS", "")
            )

            numbers.append(number)

        except ValueError:

            continue

    next_number = (
        max(numbers) + 1
        if numbers
        else 1
    )

    return f"SMS{next_number:03d}"


# =========================================================
# FARMER LOOKUP
# =========================================================

def get_farmer_by_phone(phone):

    farmers = load_farmers()

    phone = str(phone).strip()

    farmers["phone"] = (
        farmers["phone"]
        .astype(str)
        .str.replace(".0", "", regex=False)
    )

    result = farmers[
        farmers["phone"] == phone
    ]

    if result.empty:
        return None

    return result.iloc[0]


# =========================================================
# PRICE RESPONSE
# =========================================================

def price_response(crop):

    prices = load_prices()

    crop = crop.strip().title()

    result = prices[
        prices["crop"].astype(str).str.lower()
        == crop.lower()
    ].copy()

    if result.empty:

        return (
            f"No price data available for {crop}."
        )

    latest = (
        result
        .sort_values("date")
        .iloc[-1]
    )

    return (
        f"{crop} price: "
        f"Min Rs.{latest['min_price_per_kg']:.0f}/kg, "
        f"Modal Rs.{latest['modal_price_per_kg']:.0f}/kg, "
        f"Max Rs.{latest['max_price_per_kg']:.0f}/kg."
    )


# =========================================================
# DEMAND RESPONSE
# =========================================================

def demand_response(crop):

    demand = load_demand()

    crop = crop.strip().title()

    result = demand[
        demand["crop"].astype(str).str.lower()
        == crop.lower()
    ].copy()

    if result.empty:

        return (
            f"No demand data available for {crop}."
        )

    latest = (
        result
        .sort_values("date")
        .iloc[-1]
    )

    try:

        forecast = forecast_demand(
            demand_df=demand,
            district="Pune",
            crop=crop,
            forecast_days=3
        )

    except Exception:

        forecast = None

    if forecast is not None:

        return (
            f"{crop} demand in Pune: "
            f"current {forecast['current_demand_kg']:,.0f} kg, "
            f"forecast {forecast['forecast_demand_kg']:,.0f} kg "
            f"({forecast['percentage_change']}%)."
        )

    return (
        f"{crop} current demand: "
        f"{latest['demand_quantity_kg']:,.0f} kg."
    )


# =========================================================
# BEST BUYER RESPONSE
# =========================================================

def buyer_response(farmer_id, crop):

    farmers = load_farmers()
    produce = load_produce()
    buyers = load_buyers()
    demand = load_demand()

    farmer = farmers[
        farmers["farmer_id"].astype(str)
        == str(farmer_id)
    ]

    if farmer.empty:

        return "Farmer profile not found."

    farmer_produce = produce[
        (
            produce["farmer_id"].astype(str)
            == str(farmer_id)
        )
        &
        (
            produce["crop"].astype(str).str.lower()
            == crop.strip().lower()
        )
        &
        (
            produce["status"].astype(str).str.lower()
            == "available"
        )
    ].copy()

    if farmer_produce.empty:

        return (
            f"No available {crop.title()} "
            "listing found."
        )

    selected = farmer_produce.iloc[0]

    forecast = forecast_demand(
        demand_df=demand,
        district="Pune",
        crop=selected["crop"],
        forecast_days=3
    )

    forecast_kg = None

    if forecast is not None:

        forecast_kg = forecast[
            "forecast_demand_kg"
        ]

    matches = find_matches(
        selected,
        buyers,
        forecast_demand=forecast_kg
    )

    if matches.empty:

        return (
            f"No suitable buyer found for "
            f"{crop.title()}."
        )

    best = matches.iloc[0]

    return (
        f"Best buyer: {best['buyer_name']}. "
        f"Offer Rs.{best['max_price_per_kg']:.0f}/kg. "
        f"Match score {best['match_score']:.0f}%."
    )


# =========================================================
# FARMER PRODUCE RESPONSE
# =========================================================

def produce_response(farmer_id):

    produce = load_produce()

    result = produce[
        produce["farmer_id"].astype(str)
        == str(farmer_id)
    ]

    if result.empty:

        return "No produce listings found."

    messages = []

    for _, row in result.head(3).iterrows():

        messages.append(
            f"{row['crop']} "
            f"{row['quantity_kg']:.0f}kg "
            f"Grade {row['quality_grade']} "
            f"Rs.{row['expected_price_per_kg']:.0f}/kg"
        )

    return " | ".join(messages)


# =========================================================
# ORDER STATUS
# =========================================================

def status_response(farmer_id):

    from utils.transactions import (
        load_transactions
    )

    transactions = load_transactions()

    result = transactions[
        transactions["farmer_id"].astype(str)
        == str(farmer_id)
    ]

    if result.empty:

        return "No transaction history found."

    latest = (
        result
        .sort_values("date")
        .iloc[-1]
    )

    return (
        f"Latest order {latest['transaction_id']}: "
        f"{latest['status']}. "
        f"Qty {latest['quantity_kg']:.0f}kg, "
        f"Value Rs.{latest['total_value']:,.0f}."
    )


# =========================================================
# HELP
# =========================================================

def help_response():

    return (
        "Kisan Setu SMS Commands: "
        "PRICE ONION | PRICE TOMATO | "
        "DEMAND ONION | DEMAND TOMATO | "
        "BUYER ONION | BUYER TOMATO | "
        "MY PRODUCE | STATUS | HELP"
    )


# =========================================================
# PROCESS SMS
# =========================================================

def process_sms(phone, message):

    farmer = get_farmer_by_phone(phone)

    if farmer is None:

        return (
            "Phone number not registered. "
            "Please register with Kisan Setu."
        )

    farmer_id = farmer["farmer_id"]

    text = (
        str(message)
        .strip()
        .upper()
    )

    parts = text.split()

    if not parts:

        return help_response()

    command = parts[0]

    # -----------------------------------------------------
    # HELP
    # -----------------------------------------------------

    if command == "HELP":

        return help_response()

    # -----------------------------------------------------
    # PRICE
    # -----------------------------------------------------

    if command == "PRICE":

        if len(parts) < 2:

            return (
                "Usage: PRICE ONION"
            )

        crop = " ".join(parts[1:])

        return price_response(crop)

    # -----------------------------------------------------
    # DEMAND
    # -----------------------------------------------------

    if command == "DEMAND":

        if len(parts) < 2:

            return (
                "Usage: DEMAND ONION"
            )

        crop = " ".join(parts[1:])

        return demand_response(crop)

    # -----------------------------------------------------
    # BUYER
    # -----------------------------------------------------

    if command == "BUYER":

        if len(parts) < 2:

            return (
                "Usage: BUYER ONION"
            )

        crop = " ".join(parts[1:])

        return buyer_response(
            farmer_id,
            crop
        )

    # -----------------------------------------------------
    # MY PRODUCE
    # -----------------------------------------------------

    if command in [
        "MY",
        "PRODUCE"
    ]:

        return produce_response(
            farmer_id
        )

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    if command == "STATUS":

        return status_response(
            farmer_id
        )

    # -----------------------------------------------------
    # UNKNOWN COMMAND
    # -----------------------------------------------------

    return (
        "Unknown command. "
        "Send HELP for Kisan Setu commands."
    )


# =========================================================
# SEND / SIMULATE SMS
# =========================================================

def send_sms(
    phone,
    message,
    farmer_id=None
):

    df = load_sms_messages()

    message_id = generate_message_id(df)

    response = process_sms(
        phone,
        message
    )

    record = {
        "message_id": message_id,
        "phone": str(phone),
        "farmer_id": farmer_id,
        "direction": "OUTBOUND",
        "message": str(message),
        "response": response,
        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }

    df = pd.concat(
        [
            df,
            pd.DataFrame([record])
        ],
        ignore_index=True
    )

    df.to_csv(
        SMS_FILE,
        index=False
    )

    return response