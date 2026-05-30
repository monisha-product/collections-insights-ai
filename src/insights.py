import os

import google.generativeai as genai
from dotenv import load_dotenv


load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def generate_insight(question, dataframe):
    prompt = f"""
You are a collections analytics expert.

User question:
{question}

Query result:
{dataframe.to_string(index=False)}

Provide:
1. Key finding
2. Business implication
3. Recommended action

Keep the response concise and business-friendly.
Limit the response to 150 words.
"""

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    return response.text