import sqlite3
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "collections.db"


def create_sample_dataset():
    data = {
        "customer_id": [1, 2, 3, 4, 5],
        "age": [28, 35, 42, 31, 50],
        "loan_amount": [50000, 120000, 90000, 75000, 150000],
        "days_past_due": [0, 45, 90, 15, 120],
        "risk_segment": ["Low", "Medium", "High", "Medium", "High"],
        "defaulted": [0, 0, 1, 0, 1],
    }

    return pd.DataFrame(data)


def load_data_to_sqlite():
    DATA_DIR.mkdir(exist_ok=True)

    df = create_sample_dataset()

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("loan_accounts", conn, if_exists="replace", index=False)
    conn.close()

    print(f"Data loaded successfully into {DB_PATH}")


if __name__ == "__main__":
    load_data_to_sqlite()