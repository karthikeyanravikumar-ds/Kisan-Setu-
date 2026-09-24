import pandas as pd
from pathlib import Path
from datetime import date


DATA_DIR = Path(__file__).resolve().parent.parent / "data"

CONSUMER_ORDERS_FILE = DATA_DIR / "consumer_orders.csv"


COLUMNS = [
    "order_id",
    "consumer_id",
    "consumer_name",
    "produce_id",
    "farmer_id",
    "crop",
    "quantity_kg",
    "price_per_kg",
    "total_value",
    "status",
    "date"
]


def load_consumer_orders():

    if not CONSUMER_ORDERS_FILE.exists():

        return pd.DataFrame(
            columns=COLUMNS
        )

    df = pd.read_csv(
        CONSUMER_ORDERS_FILE
    )

    for column in COLUMNS:

        if column not in df.columns:
            df[column] = None

    return df[COLUMNS]


def generate_order_id(df):

    if df.empty:
        return "C001"

    numbers = []

    for order_id in df["order_id"].astype(str):

        try:

            number = int(
                order_id.replace("C", "")
            )

            numbers.append(number)

        except ValueError:

            continue

    next_number = (
        max(numbers) + 1
        if numbers
        else 1
    )

    return f"C{next_number:03d}"


def create_consumer_order(
    consumer_id,
    consumer_name,
    produce_id,
    farmer_id,
    crop,
    quantity_kg,
    price_per_kg
):

    df = load_consumer_orders()

    order_id = generate_order_id(df)

    quantity_kg = float(quantity_kg)
    price_per_kg = float(price_per_kg)

    total_value = (
        quantity_kg *
        price_per_kg
    )

    order = {
        "order_id": order_id,
        "consumer_id": consumer_id,
        "consumer_name": consumer_name,
        "produce_id": produce_id,
        "farmer_id": farmer_id,
        "crop": crop,
        "quantity_kg": quantity_kg,
        "price_per_kg": price_per_kg,
        "total_value": total_value,
        "status": "Order Placed",
        "date": date.today().strftime(
            "%Y-%m-%d"
        )
    }

    df = pd.concat(
        [
            df,
            pd.DataFrame([order])
        ],
        ignore_index=True
    )

    df.to_csv(
        CONSUMER_ORDERS_FILE,
        index=False
    )

    return order


def update_consumer_order_status(
    order_id,
    new_status
):

    df = load_consumer_orders()

    if df.empty:
        return False

    mask = (
        df["order_id"].astype(str)
        == str(order_id)
    )

    if not mask.any():
        return False

    df.loc[
        mask,
        "status"
    ] = new_status

    df.to_csv(
        CONSUMER_ORDERS_FILE,
        index=False
    )

    return True