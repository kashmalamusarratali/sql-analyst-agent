import os
import sqlite3
from dotenv import load_dotenv
from openai import OpenAI
import re

load_dotenv()

BLOCKED = ["insert", "update", "delete", "drop", "alter", "create",
           "replace", "pragma", "attach", "detach", "vacuum"]


def validate_sql(sql):
    cleaned = sql.strip().rstrip(";").strip()
    if ";" in cleaned:
        raise ValueError("Only one SQL statement is allowed.")
    if not re.match(r"^(select|with)\b", cleaned, re.IGNORECASE):
        raise ValueError("Only SELECT queries are allowed.")
    for word in BLOCKED:
        if re.search(rf"\b{word}\b", cleaned, re.IGNORECASE):
            raise ValueError(f"Blocked keyword: {word}")
    return cleaned

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)
MODEL = os.getenv("LLM_MODEL")
DB_PATH = "ecommerce.db"


def get_schema():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    conn.close()
    return "\n\n".join(r[0] for r in rows)


def question_to_sql(question, bad_sql=None, error=None):
    system_prompt = f"""You are a SQL expert. Write ONE SQLite query that answers the user's question.

Database schema:
{get_schema()}

Rules:
- Return only the SQL query. No explanation, no markdown.
- Use only tables and columns from the schema.
- Revenue = SUM(products.price * order_items.quantity).
"""
  
    messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": question},
]
    if bad_sql:
        messages.append({"role": "assistant", "content": bad_sql})
    messages.append({
        "role": "user",
        "content": f"That query failed with this error: {error}\nReturn only the corrected SQLite query.",
    })

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0,
    )
    sql = response.choices[0].message.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql
def run_sql(sql):
    sql = validate_sql(sql)
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cur = conn.cursor()
    cur.execute(sql)
    columns = [d[0] for d in cur.description]
    rows = cur.fetchall()
    conn.close()
    return columns, rows

def ask(question, max_retries=2):
    sql = question_to_sql(question)
    for attempt in range(max_retries + 1):
        try:
            columns, rows = run_sql(sql)
            return sql, columns, rows
        except (sqlite3.Error, ValueError) as e:
            if attempt == max_retries:
                raise
            sql = question_to_sql(question, bad_sql=sql, error=str(e))


if __name__ == "__main__":
    question = input("Ask a question: ")
    sql, columns, rows = ask(question)

    print("\nSQL:")
    print(sql)
    print("\nResult:")
    print(columns)
    for row in rows[:20]:
        print(row)