import os
import sqlite3
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "collections.db"

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def get_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    tables = [
        "customers",
        "loans",
        "repayments",
        "collections",
        "collection_agents",
        "collection_assignments",
    ]

    schema = ""

    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()

        schema += f"\nTable: {table}\n"

        for col in columns:
            schema += f"- {col[1]} ({col[2]})\n"

    conn.close()
    return schema


def generate_sql(user_question):
    schema = get_schema()

    prompt = f"""
You are a SQL analyst for a loan collections analytics product.

Generate a SQLite SQL query for the user's question.

Rules:
- Use only the tables and columns listed below.
- Return only SQL.
- Do not include markdown.
- Do not explain the query.
- Use SQLite syntax.
- Limit results to 20 rows where appropriate.

Database schema:
{schema}

User question:
{user_question}
"""

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    sql = response.text.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()

    return sql