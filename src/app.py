import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "collections.db"


QUESTION_SQL_MAP = {
    "Which risk segment has the highest default rate?": """
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
        JOIN loans l ON c.customer_id = l.customer_id
        GROUP BY c.risk_segment
        ORDER BY default_rate DESC;
    """,
    "Which collection stage has recovered the highest amount?": """
        SELECT
            collection_stage,
            SUM(recovered_amount) AS total_recovered_amount,
            COUNT(*) AS collection_events
        FROM collections
        GROUP BY collection_stage
        ORDER BY total_recovered_amount DESC;
    """,
    "Which states have the highest number of defaulted loans?": """
        SELECT
            c.state,
            COUNT(DISTINCT l.loan_id) AS total_loans,
            SUM(CASE WHEN l.loan_status IN ('Defaulted', 'Written Off') THEN 1 ELSE 0 END) AS defaulted_loans
        FROM customers c
        JOIN loans l ON c.customer_id = l.customer_id
        GROUP BY c.state
        ORDER BY defaulted_loans DESC;
    """
}


def run_query(query):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def generate_basic_insight(question, df):
    if df.empty:
        return "No data found for this question."

    top_row = df.iloc[0].to_dict()
    return f"For the question '{question}', the highest value is observed for: {top_row}."


st.set_page_config(page_title="Collections Insights AI", layout="wide")

st.title("Collections Insights AI")
st.write(
    "Ask business questions about loan collections, recovery, delinquency, and portfolio risk."
)

question = st.selectbox(
    "Choose a business question",
    list(QUESTION_SQL_MAP.keys())
)

if st.button("Generate Insight"):
    sql = QUESTION_SQL_MAP[question]
    result = run_query(sql)

    st.subheader("SQL Query")
    st.code(sql, language="sql")

    st.subheader("Query Result")
    st.dataframe(result)

    st.subheader("Business Insight")
    st.write(generate_basic_insight(question, result))