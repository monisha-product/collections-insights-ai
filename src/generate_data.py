import sqlite3
import random
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "collections.db"

random.seed(42)


def generate_customers(n=1000):
    states = ["Karnataka", "Maharashtra", "Delhi", "Tamil Nadu", "Telangana", "Gujarat"]
    risk_segments = ["Low", "Medium", "High"]

    data = []

    for i in range(1, n + 1):
        data.append({
            "customer_id": i,
            "age": random.randint(22, 60),
            "state": random.choice(states),
            "monthly_income": random.randint(25000, 200000),
            "risk_segment": random.choices(risk_segments, weights=[45, 35, 20])[0],
            "customer_since": datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1500))
        })

    return pd.DataFrame(data)


def generate_loans(customers_df):
    loan_statuses = ["Active", "Closed", "Defaulted", "Written Off"]
    loan_grades = ["A", "B", "C", "D", "E"]

    data = []
    loan_id = 1

    for _, customer in customers_df.iterrows():
        num_loans = random.choice([1, 1, 1, 2])

        for _ in range(num_loans):
            data.append({
                "loan_id": loan_id,
                "customer_id": customer["customer_id"],
                "loan_amount": random.randint(50000, 800000),
                "interest_rate": round(random.uniform(9.5, 28.0), 2),
                "loan_grade": random.choice(loan_grades),
                "loan_status": random.choices(
                    loan_statuses,
                    weights=[50, 25, 18, 7]
                )[0],
                "disbursement_date": datetime(2021, 1, 1) + timedelta(days=random.randint(0, 1200))
            })
            loan_id += 1

    return pd.DataFrame(data)


def generate_repayments(loans_df):
    data = []
    repayment_id = 1

    for _, loan in loans_df.iterrows():
        num_payments = random.randint(3, 18)

        for _ in range(num_payments):
            payment_amount = random.randint(2000, 50000)

            data.append({
                "repayment_id": repayment_id,
                "loan_id": loan["loan_id"],
                "payment_date": loan["disbursement_date"] + timedelta(days=random.randint(30, 720)),
                "payment_amount": payment_amount,
                "principal_paid": round(payment_amount * random.uniform(0.65, 0.9), 2),
                "interest_paid": round(payment_amount * random.uniform(0.1, 0.35), 2)
            })
            repayment_id += 1

    return pd.DataFrame(data)


def generate_collections(loans_df):
    stages = ["Reminder", "Soft Collection", "Hard Collection", "Legal Notice", "Recovery Agency"]
    outcomes = ["Paid", "Promise To Pay", "No Response", "Dispute", "Escalated"]

    data = []
    collection_id = 1

    risky_loans = loans_df[loans_df["loan_status"].isin(["Defaulted", "Written Off", "Active"])]

    for _, loan in risky_loans.iterrows():
        num_events = random.randint(1, 6)

        for _ in range(num_events):
            data.append({
                "collection_id": collection_id,
                "loan_id": loan["loan_id"],
                "days_past_due": random.choice([0, 15, 30, 60, 90, 120, 180]),
                "collection_stage": random.choice(stages),
                "contact_date": datetime(2023, 1, 1) + timedelta(days=random.randint(0, 700)),
                "outcome": random.choice(outcomes),
                "recovered_amount": random.randint(0, 80000)
            })
            collection_id += 1

    return pd.DataFrame(data)


def save_to_sqlite():
    DATA_DIR.mkdir(exist_ok=True)

    customers = generate_customers()
    loans = generate_loans(customers)
    repayments = generate_repayments(loans)
    collections = generate_collections(loans)

    conn = sqlite3.connect(DB_PATH)

    customers.to_sql("customers", conn, if_exists="replace", index=False)
    loans.to_sql("loans", conn, if_exists="replace", index=False)
    repayments.to_sql("repayments", conn, if_exists="replace", index=False)
    collections.to_sql("collections", conn, if_exists="replace", index=False)

    conn.close()

    print("Database created successfully")
    print(f"Path: {DB_PATH}")
    print(f"Customers: {len(customers)}")
    print(f"Loans: {len(loans)}")
    print(f"Repayments: {len(repayments)}")
    print(f"Collections: {len(collections)}")


if __name__ == "__main__":
    save_to_sqlite()