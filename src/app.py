from ai_sql import generate_sql
from insights import generate_insight
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
    """,

    "Which collection agents recovered the highest amount?": """
        SELECT
            ag.agent_name,
            ag.region,
            ag.experience_years,
            SUM(col.recovered_amount) AS total_recovered_amount,
            COUNT(DISTINCT col.collection_id) AS collection_events
        FROM collection_agents ag
        JOIN collection_assignments ca ON ag.agent_id = ca.agent_id
        JOIN collections col ON ca.loan_id = col.loan_id
        GROUP BY ag.agent_id, ag.agent_name, ag.region, ag.experience_years
        ORDER BY total_recovered_amount DESC
        LIMIT 10;
    """,

    "Which agents have the highest paid outcome rate?": """
        SELECT
            ag.agent_name,
            ag.region,
            COUNT(*) AS total_collection_events,
            SUM(CASE WHEN col.outcome = 'Paid' THEN 1 ELSE 0 END) AS paid_events,
            ROUND(
                100.0 * SUM(CASE WHEN col.outcome = 'Paid' THEN 1 ELSE 0 END) / COUNT(*),
                2
            ) AS paid_outcome_rate
        FROM collection_agents ag
        JOIN collection_assignments ca ON ag.agent_id = ca.agent_id
        JOIN collections col ON ca.loan_id = col.loan_id
        GROUP BY ag.agent_id, ag.agent_name, ag.region
        ORDER BY paid_outcome_rate DESC
        LIMIT 10;
    """
}


def run_query(query):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def show_dynamic_chart(df):
    if df.empty or len(df.columns) < 2:
        return

    numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
    non_numeric_columns = df.select_dtypes(exclude=["number"]).columns.tolist()

    if not numeric_columns or not non_numeric_columns:
        return

    x_col = non_numeric_columns[0]
    y_col = numeric_columns[-1]

    st.subheader("Chart View")
    chart_data = df[[x_col, y_col]].set_index(x_col)
    st.bar_chart(chart_data)


def generate_basic_insight(question, df):
    if df.empty:
        return "No data found for this question."

    top_row = df.iloc[0].to_dict()
    return f"For the question '{question}', the highest value is observed for: {top_row}."


def match_question(user_question):
    user_question_lower = user_question.lower()

    for question in QUESTION_SQL_MAP.keys():
        question_words = question.lower().replace("?", "").split()

        matched_words = [
            word for word in question_words
            if word in user_question_lower and len(word) > 3
        ]

        if len(matched_words) >= 2:
            return question

    return None


st.set_page_config(page_title="Collections Insights AI", layout="wide")

st.sidebar.title("Suggested Questions")

suggested_questions = [
    "Which risk segment has the highest default rate?",
    "Which collection agents recovered the highest amount?",
    "Which states have the highest number of defaulted loans?",
    "Which collection stage has recovered the highest amount?",
    "Which agents have the highest paid outcome rate?",
    "Which region has the best recovery performance?",
    "Which loan grades contribute most to defaults?"
]

selected_question = st.sidebar.radio(
    "Try one of these:",
    suggested_questions
)

st.write(
    "Ask business questions about loan collections, recovery, delinquency, "
    "agent productivity, and portfolio risk."
)

st.markdown("### Example questions")
st.markdown(
    """
- Which risk segment has the highest default rate?
- Which collection stage has recovered the highest amount?
- Which states have the highest number of defaulted loans?
- Which collection agents recovered the highest amount?
- Which agents have the highest paid outcome rate?
"""
)

user_question = st.text_input(
    "Ask a question about collections data",
    value=selected_question
)

if st.button("Generate Insight"):
    if not user_question.strip():
        st.warning("Please enter a question.")
    else:
        try:
            sql = generate_sql(user_question)
            result = run_query(sql)

            st.subheader("Generated SQL Query")
            st.code(sql, language="sql")

            st.subheader("Query Result")
            st.dataframe(result)
            
            show_dynamic_chart(result)

            try:
                st.subheader("AI Recommendation")

                ai_insight = generate_insight(
                    user_question,
                    result
                )

                st.write(ai_insight)

            except Exception:
                st.info(
                    "AI recommendations are temporarily unavailable. "
                    "Query results are still displayed."
                )

        except Exception as e:
            st.error("Something went wrong while generating or running the SQL query.")
            st.write(e)