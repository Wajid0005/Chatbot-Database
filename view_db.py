import sqlite3
import pandas as pd

conn = sqlite3.connect("chatbot.db")

df = pd.read_sql_query("""
SELECT
    id,
    timestamp,
    user_query,
    input_tokens,
    output_tokens,
    total_tokens,
    estimated_cost,
    model_name
FROM chat_history
""", conn)

print(df.to_markdown(index=False))

print("\n===== SUMMARY =====")
print("Total Chats:", len(df))
print("Total Tokens:", df["total_tokens"].sum())
print("Total Cost:", df["estimated_cost"].sum())