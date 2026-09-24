import pandas as pd
from pathlib import Path
from datetime import date


# ============================================================
# PATH
# ============================================================

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

TRANSACTIONS_FILE = DATA_DIR / "transactions.csv"


# ============================================================
# TRANSACTION COLUMNS
# ============================================================

TRANSACTION_COLUMNS = [
    "transaction_id",
    "farmer_id",
    "buyer_id",
    "produce_id",
    "quantity_kg",
    "price_per_kg",
    "total_value",
    "status",
    "date"
]


# ============================================================
# LOAD TRANSACTIONS
# ============================================================

def load_transactions():

    if not TRANSACTIONS_FILE.exists():

        return pd.DataFrame(
            columns=TRANSACTION_COLUMNS
        )

    df = pd.read_csv(
        TRANSACTIONS_FILE
    )

    # Make sure all expected columns exist
    for column in TRANSACTION_COLUMNS:

        if column not in df.columns:
            df[column] = None

    return df[TRANSACTION_COLUMNS]


# ============================================================
# GENERATE TRANSACTION ID
# ============================================================

def generate_transaction_id(df):

    if df.empty:

        return "T001"

    numbers = []

    for transaction_id in df[
        "transaction_id"
    ].astype(str):

        try:

            number = int(
                transaction_id.replace(
                    "T",
                    ""
                )
            )

            numbers.append(number)

        except ValueError:

            continue

    if numbers:

        next_number = max(numbers) + 1

    else:

        next_number = 1

    return f"T{next_number:03d}"


# ============================================================
# CREATE TRANSACTION
# ============================================================

def create_transaction(
    farmer_id,
    buyer_id,
    produce_id,
    quantity_kg,
    price_per_kg,
    status="Order Placed"
):

    df = load_transactions()

    transaction_id = generate_transaction_id(
        df
    )

    quantity_kg = float(
        quantity_kg
    )

    price_per_kg = float(
        price_per_kg
    )

    total_value = (
        quantity_kg *
        price_per_kg
    )

    transaction = {
        "transaction_id": transaction_id,
        "farmer_id": farmer_id,
        "buyer_id": buyer_id,
        "produce_id": produce_id,
        "quantity_kg": quantity_kg,
        "price_per_kg": price_per_kg,
        "total_value": total_value,
        "status": status,
        "date": date.today().strftime(
            "%Y-%m-%d"
        )
    }

    df = pd.concat(
        [
            df,
            pd.DataFrame(
                [transaction]
            )
        ],
        ignore_index=True
    )

    df.to_csv(
        TRANSACTIONS_FILE,
        index=False
    )

    return transaction


# ============================================================
# UPDATE TRANSACTION STATUS
# ============================================================

def update_transaction_status(
    transaction_id,
    new_status
):

    df = load_transactions()

    if df.empty:

        return False

    mask = (
        df["transaction_id"].astype(str)
        == str(transaction_id)
    )

    if not mask.any():

        return False

    df.loc[
        mask,
        "status"
    ] = new_status

    df.to_csv(
        TRANSACTIONS_FILE,
        index=False
    )

    return True


# ============================================================
# GET TRANSACTIONS FOR BUYER
# ============================================================

def get_buyer_transactions(
    buyer_id
):

    df = load_transactions()

    if df.empty:

        return df

    return df[
        df["buyer_id"].astype(str)
        == str(buyer_id)
    ].copy()


# ============================================================
# GET TRANSACTIONS FOR FARMER
# ============================================================

def get_farmer_transactions(
    farmer_id
):

    df = load_transactions()

    if df.empty:

        return df

    return df[
        df["farmer_id"].astype(str)
        == str(farmer_id)
    ].copy()