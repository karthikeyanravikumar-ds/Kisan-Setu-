import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_data(filename):
    return pd.read_csv(DATA_DIR / filename)


def load_farmers():
    return load_data("farmers.csv")


def load_buyers():
    return load_data("buyers.csv")


def load_produce():
    return load_data("produce.csv")


def load_prices():
    return load_data("prices.csv")


def load_market_prices():
    """Load normalized market prices from processed dataset with fallback to prices.csv."""
    proc_file = DATA_DIR / "processed" / "market_prices.csv"
    if proc_file.exists():
        try:
            df = pd.read_csv(proc_file)
            if not df.empty:
                return df
        except Exception:
            pass
    return load_prices()


def load_demand():
    return load_data("demand.csv")


def load_logistics():
    return load_data("logistics.csv")


def load_schemes():
    return load_data("schemes.csv")


def load_transactions():
    return load_data("transactions.csv")


def load_feedback():
    return load_data("feedback.csv")


def load_buyer_requirements():
    req_file = DATA_DIR / "buyer_requirements.csv"
    if not req_file.exists():
        return pd.DataFrame(columns=[
            "requirement_id", "buyer_id", "buyer_name", "buyer_type", "crop",
            "quantity_kg", "minimum_quality", "maximum_price_per_kg", "delivery_location",
            "required_date", "additional_requirements", "status", "posted_date"
        ])
    return pd.read_csv(req_file)


def load_payments():
    pay_file = DATA_DIR / "payments.csv"
    if not pay_file.exists():
        return pd.DataFrame(columns=[
            "payment_id", "transaction_id", "buyer_id", "farmer_id",
            "gross_amount", "logistics_cost", "platform_fee", "net_settlement",
            "payment_status", "settlement_status", "payment_date", "settlement_date"
        ])
    return pd.read_csv(pay_file)