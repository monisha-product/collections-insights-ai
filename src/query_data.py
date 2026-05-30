import sqlite3
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "collections.db"


def run_query(query):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


if __name__ == "__main__":
    query = """
    SELECT
        c.risk_segment,
        COUNT(DISTINCT l.loan_id) AS total_loans,
        SUM(CASE WHEN l.loan_status IN ('Defaulted', 'Written Off') THEN 1 ELSE 0 END) AS bad_loans,
        ROUND(
            100.0 * SUM(CASE WHEN l.loan_status IN ('Defaulted', 'Written Off') THEN 1 ELSE 0 END)
            / COUNT(DISTINCT l.loan_id),
            2
        ) AS default_rate
    FROM customers c
    JOIN loans l
        ON c.customer_id = l.customer_id
    GROUP BY c.risk_segment
    ORDER BY default_rate DESC;
    """

    result = run_query(query)
    print(result)