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
    """,

    "Which agents have the highest promise-to-pay conversion rate?": """
        SELECT
            ag.agent_name,
            ag.region,
            COUNT(ptp.ptp_id) AS total_promises,
            SUM(CASE WHEN ptp.status = 'Kept' THEN 1 ELSE 0 END) AS kept_promises,
            ROUND(
                100.0 * SUM(CASE WHEN ptp.status = 'Kept' THEN 1 ELSE 0 END) / COUNT(ptp.ptp_id),
                2
            ) AS ptp_conversion_rate
        FROM promise_to_pay ptp
        JOIN collection_agents ag ON ptp.agent_id = ag.agent_id
        GROUP BY ag.agent_id, ag.agent_name, ag.region
        HAVING COUNT(ptp.ptp_id) >= 5
        ORDER BY ptp_conversion_rate DESC
        LIMIT 10;
    """,

    "Which collection channel is most effective?": """
        SELECT
            channel,
            COUNT(*) AS total_attempts,
            SUM(CASE WHEN outcome IN ('Paid', 'Promise to Pay') THEN 1 ELSE 0 END) AS successful_attempts,
            ROUND(
                100.0 * SUM(CASE WHEN outcome IN ('Paid', 'Promise to Pay') THEN 1 ELSE 0 END) / COUNT(*),
                2
            ) AS success_rate
        FROM collection_attempts
        GROUP BY channel
        ORDER BY success_rate DESC;
    """,

    "Which region has the highest broken promise rate?": """
        SELECT
            ag.region,
            COUNT(ptp.ptp_id) AS total_promises,
            SUM(CASE WHEN ptp.status = 'Broken' THEN 1 ELSE 0 END) AS broken_promises,
            ROUND(
                100.0 * SUM(CASE WHEN ptp.status = 'Broken' THEN 1 ELSE 0 END) / COUNT(ptp.ptp_id),
                2
            ) AS broken_promise_rate
        FROM promise_to_pay ptp
        JOIN collection_agents ag ON ptp.agent_id = ag.agent_id
        GROUP BY ag.region
        ORDER BY broken_promise_rate DESC;
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

if "last_question" not in st.session_state:
    st.session_state.last_question = None

if "last_sql" not in st.session_state:
    st.session_state.last_sql = None

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "last_ai_recommendation" not in st.session_state:
    st.session_state.last_ai_recommendation = None


st.sidebar.title("Suggested Questions")

suggested_questions = [
    "Which risk segment has the highest default rate?",
    "Which collection agents recovered the highest amount?",
    "Which states have the highest number of defaulted loans?",
    "Which collection stage has recovered the highest amount?",
    "Which agents have the highest paid outcome rate?",
    "Which region has the best recovery performance?",
    "Which loan grades contribute most to defaults?",
    "Which agents have the highest promise-to-pay conversion rate?",
    "Which collection channel is most effective?",
    "Which region has the highest broken promise rate?"
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
- Which agents have the highest promise-to-pay conversion rate?
- Which collection channel is most effective?
- Which region has the highest broken promise rate?
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
            try:
                sql = generate_sql(user_question)
                st.success("SQL generated using Gemini AI.")
            except Exception:
                matched_question = match_question(user_question)

                if matched_question:
                    sql = QUESTION_SQL_MAP[matched_question]
                    st.info("Gemini quota unavailable. Using predefined query fallback.")
                else:
                    st.error(
                        "Gemini quota is unavailable and no fallback query matched your question. "
                        "Try one of the suggested questions."
                    )
                    st.stop()

            result = run_query(sql)

            st.session_state.last_question = user_question
            st.session_state.last_sql = sql
            st.session_state.last_result = result
            st.session_state.last_ai_recommendation = None

        except Exception as e:
            st.error("Something went wrong while generating or running the SQL query.")
            st.write(e)


if st.session_state.last_result is not None:
    st.subheader("Generated SQL Query")
    st.code(st.session_state.last_sql, language="sql")

    st.subheader("Query Result")
    st.dataframe(st.session_state.last_result)

    show_dynamic_chart(st.session_state.last_result)

    st.subheader("AI Recommendation")

    if st.button("Generate AI Recommendation"):
        try:
            ai_insight = generate_insight(
                st.session_state.last_question,
                st.session_state.last_result
            )
            st.session_state.last_ai_recommendation = ai_insight

        except Exception:
            st.info(
                "AI recommendations are temporarily unavailable. "
                "Query results are still displayed."
            )

    if st.session_state.last_ai_recommendation:
        st.write(st.session_state.last_ai_recommendation)
    else:
        st.info("Click 'Generate AI Recommendation' to create an AI recommendation.")