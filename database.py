import sqlite3

def save_chat(
    question,
    answer,
    input_tokens,
    output_tokens,
    total_tokens,
    cost,
    model_name
):
    conn = sqlite3.connect("chatbot.db")

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO chat_history
    (
    user_query,
    ai_response,
    input_tokens,
    output_tokens,
    total_tokens,
    estimated_cost,
    model_name
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
    (
        question,
        answer,
        input_tokens,
        output_tokens,
        total_tokens,
        cost,
        model_name
    ))

    conn.commit()
    conn.close()