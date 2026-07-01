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

def generate_agents(n=25):
    regions = ["South", "West", "North", "East"]
    data = []

    for i in range(1, n + 1):
        data.append({
            "agent_id": i,
            "agent_name": f"Agent {i}",
            "region": random.choice(regions),
            "experience_years": random.randint(1, 10)
        })

    return pd.DataFrame(data)


def generate_assignments(loans_df, agents_df):
    data = []
    assignment_id = 1

    eligible_loans = loans_df[loans_df["loan_status"].isin(["Active", "Defaulted", "Written Off"])]

    for _, loan in eligible_loans.iterrows():
        agent = agents_df.sample(1).iloc[0]

        data.append({
            "assignment_id": assignment_id,
            "loan_id": loan["loan_id"],
            "agent_id": agent["agent_id"],
            "assigned_date": datetime(2023, 1, 1) + timedelta(days=random.randint(0, 700))
        })

        assignment_id += 1

    return pd.DataFrame(data)

def generate_collection_attempts(loans_df, customers_df, agents_df):
    attempts = []

    state_region_map = {
        "Karnataka": "South",
        "Tamil Nadu": "South",
        "Maharashtra": "West",
        "Gujarat": "West",
        "Delhi": "North",
        "Telangana": "South",
    }

    channels = ["Phone", "WhatsApp", "SMS", "Email", "Field Visit"]
    outcomes = [
        "Connected",
        "No Answer",
        "Promise to Pay",
        "Paid",
        "Refused",
        "Wrong Number",
        "Callback Requested",
    ]

    outcome_weights = [0.30, 0.22, 0.20, 0.08, 0.08, 0.04, 0.08]

    eligible_loans = loans_df[
        loans_df["loan_status"].isin(["Active", "Defaulted", "Written Off"])
    ]

    for _, loan in eligible_loans.iterrows():
        loan_id = loan["loan_id"]
        customer_id = loan["customer_id"]

        customer = customers_df[customers_df["customer_id"] == customer_id].iloc[0]
        customer_state = customer["state"]
        region = state_region_map.get(customer_state, "South")

        region_agents = agents_df[agents_df["region"] == region]
        agent = region_agents.sample(1).iloc[0] if not region_agents.empty else agents_df.sample(1).iloc[0]

        num_attempts = random.randint(1, 5)
        start_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 300))

        for i in range(num_attempts):
            attempt_datetime = start_date + timedelta(days=i * random.randint(2, 7))
            channel = random.choice(channels)
            outcome = random.choices(outcomes, weights=outcome_weights, k=1)[0]

            follow_up_required = outcome in [
                "No Answer",
                "Promise to Pay",
                "Callback Requested",
                "Refused",
            ]

            follow_up_date = (
                attempt_datetime + timedelta(days=random.randint(1, 5))
                if follow_up_required
                else None
            )

            attempts.append({
                "attempt_id": f"ATT{len(attempts) + 1:06d}",
                "loan_id": loan_id,
                "customer_id": customer_id,
                "agent_id": agent["agent_id"],
                "attempt_datetime": attempt_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "channel": channel,
                "outcome": outcome,
                "duration_minutes": random.randint(2, 25),
                "follow_up_required": int(follow_up_required),
                "follow_up_date": follow_up_date.strftime("%Y-%m-%d") if follow_up_date else None,
                "remarks": f"{outcome} via {channel}",
            })

    return pd.DataFrame(attempts)

def generate_promise_to_pay(collection_attempts_df, loans_df):
    ptp_records = []

    ptp_attempts = collection_attempts_df[
        collection_attempts_df["outcome"] == "Promise to Pay"
    ]

    statuses = ["Kept", "Broken", "Partial", "Pending"]
    status_weights = [0.50, 0.25, 0.15, 0.10]

    for _, attempt in ptp_attempts.iterrows():
        loan = loans_df[loans_df["loan_id"] == attempt["loan_id"]].iloc[0]

        promise_date = datetime.strptime(
            attempt["attempt_datetime"],
            "%Y-%m-%d %H:%M:%S"
        )

        promised_payment_date = promise_date + timedelta(days=random.randint(2, 10))
        promised_amount = round(random.uniform(3000, 25000), 2)

        status = random.choices(statuses, weights=status_weights, k=1)[0]

        if status == "Kept":
            actual_payment_date = promised_payment_date + timedelta(days=random.randint(-1, 2))
            actual_paid_amount = promised_amount

        elif status == "Partial":
            actual_payment_date = promised_payment_date + timedelta(days=random.randint(1, 5))
            actual_paid_amount = round(promised_amount * random.uniform(0.4, 0.8), 2)

        elif status == "Broken":
            actual_payment_date = None
            actual_paid_amount = 0

        else:
            actual_payment_date = None
            actual_paid_amount = 0

        ptp_records.append({
            "ptp_id": f"PTP{len(ptp_records) + 1:06d}",
            "loan_id": attempt["loan_id"],
            "customer_id": attempt["customer_id"],
            "agent_id": attempt["agent_id"],
            "promise_date": promise_date.strftime("%Y-%m-%d"),
            "promised_payment_date": promised_payment_date.strftime("%Y-%m-%d"),
            "promised_amount": promised_amount,
            "actual_payment_date": actual_payment_date.strftime("%Y-%m-%d") if actual_payment_date else None,
            "actual_paid_amount": actual_paid_amount,
            "status": status
        })

    return pd.DataFrame(ptp_records)

def save_to_sqlite():
    DATA_DIR.mkdir(exist_ok=True)

    customers = generate_customers()
    loans = generate_loans(customers)
    repayments = generate_repayments(loans)
    collections = generate_collections(loans)
    agents = generate_agents()
    assignments = generate_assignments(loans, agents)
    collection_attempts = generate_collection_attempts(loans, customers, agents)
    promise_to_pay = generate_promise_to_pay(collection_attempts, loans)

    conn = sqlite3.connect(DB_PATH)

    customers.to_sql("customers", conn, if_exists="replace", index=False)
    loans.to_sql("loans", conn, if_exists="replace", index=False)
    repayments.to_sql("repayments", conn, if_exists="replace", index=False)
    collections.to_sql("collections", conn, if_exists="replace", index=False)
    agents.to_sql("collection_agents", conn, if_exists="replace", index=False)
    assignments.to_sql("collection_assignments", conn, if_exists="replace", index=False)
    collection_attempts.to_sql("collection_attempts", conn, if_exists="replace", index=False)
    promise_to_pay.to_sql("promise_to_pay", conn, if_exists="replace", index=False)

    conn.close()

    print("Database created successfully")
    print(f"Path: {DB_PATH}")
    print(f"Customers: {len(customers)}")
    print(f"Loans: {len(loans)}")
    print(f"Repayments: {len(repayments)}")
    print(f"Collections: {len(collections)}")
    print(f"Agents: {len(agents)}")
    print(f"Assignments: {len(assignments)}")
    print(f"Collection Attempts: {len(collection_attempts)}")
    print(f"Promise To Pay: {len(promise_to_pay)}")


if __name__ == "__main__":
    save_to_sqlite()