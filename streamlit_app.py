import streamlit as st
import sqlite3
import pandas as pd
import datetime
import os
from token_counter import count_token
from database import save_chat

# Database Auto-Initialization
def init_db():
    conn = sqlite3.connect("chatbot.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        user_query TEXT,
        ai_response TEXT,
        input_tokens INTEGER,
        output_tokens INTEGER,
        total_tokens INTEGER,
        estimated_cost REAL,
        model_name TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# Must be the first streamlit call
st.set_page_config(
    page_title="Wajid's REENO chat bot & Logs Dashboard",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load LLM model lazily to speed up start and page switching
@st.cache_resource
def get_model():
    from model import model
    return model

# Global Styles
st.markdown("""
<style>
    /* Primary brand colors and styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 700;
    }
    .stProgress > div > div > div > div {
        background-color: #4F46E5;
    }
    
    /* Custom style for Chat container */
    .stats-container {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px;
        font-size: 0.85rem;
        color: #64748b;
        margin-top: 5px;
    }
    
    /* Dark mode adjustments for stats container */
    @media (prefers-color-scheme: dark) {
        .stats-container {
            background-color: #1e293b;
            border: 1px solid #334155;
            color: #94a3b8;
        }
    }
</style>
""", unsafe_allow_html=True)

# Navigation
st.sidebar.markdown("""
<div style="text-align: center; padding: 10px 0;">
    <h2 style="margin: 0; color: #4F46E5;">🤖 Qwen AI Suite</h2>
    <p style="font-size: 0.85rem; color: #64748b; margin-top: 5px;">LangChain & SQLite Integration</p>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio(
    "Navigate",
    ["💬 Wajid's REENO chat bot", "📊 Database History & Logs"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
### Model Specifications
- **Model:** Qwen 2.5 7B Instruct
- **Provider:** Hugging Face Hub
- **Database:** SQLite3 (`chatbot.db`)
""")

# Database helper functions
def get_db_connection():
    return sqlite3.connect("chatbot.db")

def fetch_logs():
    conn = get_db_connection()
    df = pd.read_sql_query("""
        SELECT 
            id, 
            timestamp, 
            user_query, 
            ai_response, 
            input_tokens, 
            output_tokens, 
            total_tokens, 
            estimated_cost, 
            model_name 
        FROM chat_history 
        ORDER BY id DESC
    """, conn)
    conn.close()
    return df

def clear_logs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history")
    conn.commit()
    conn.close()

# ----------------- PAGE 1: CHAT ASSISTANT -----------------
if page == "💬 Wajid's REENO chat bot":
    st.markdown("# 💬 Wajid's REENO chat bot")
    st.markdown("Ask anything to the Qwen 2.5 7B model. Your query, response, and token usage will be logged automatically.")

    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "stats" in msg:
                st.markdown(
                    f"""<div class='stats-container'>
                        Tokens: {msg['stats']['total']} (In: {msg['stats']['in']} | Out: {msg['stats']['out']}) 
                        | Cost: ${msg['stats']['cost']:.6f}
                    </div>""", 
                    unsafe_allow_html=True
                )

    # React to user input
    if prompt := st.chat_input("What is on your mind?"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to session state
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            status_text = st.status("Thinking...", expanded=True)
            
            try:
                # Load model
                model = get_model()
                
                status_text.update(label="Generating response...", state="running")
                # Invoke LLM
                response = model.invoke(prompt)
                full_response = response.content
                
                status_text.update(label="Calculating tokens & saving...", state="running")
                # Count tokens
                in_tokens = count_token(prompt)
                out_tokens = count_token(full_response)
                total_tokens = in_tokens + out_tokens
                
                # Qwen 2.5 7B cost estimate: let's set $0.00007 per 1K tokens ($0.07 per 1M)
                cost = (total_tokens / 1000.0) * 0.00007
                
                # Save to database
                save_chat(
                    prompt, 
                    full_response, 
                    in_tokens, 
                    out_tokens, 
                    total_tokens, 
                    cost, 
                    "Qwen/Qwen2.5-7B-Instruct"
                )
                
                # Render answer
                status_text.update(label="Finished successfully!", state="complete", expanded=False)
                message_placeholder.markdown(full_response)
                
                stats_html = f"""<div class='stats-container'>
                    Tokens: {total_tokens} (In: {in_tokens} | Out: {out_tokens}) 
                    | Cost: ${cost:.6f}
                </div>"""
                st.markdown(stats_html, unsafe_allow_html=True)
                
                # Save to session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "stats": {
                        "in": in_tokens,
                        "out": out_tokens,
                        "total": total_tokens,
                        "cost": cost
                    }
                })
                
            except Exception as e:
                status_text.update(label="Error occurred!", state="error", expanded=True)
                st.error(f"Error invoking model: {str(e)}")
                
                # Diagnostics box to troubleshoot secrets
                with st.expander("🛠️ Credentials Diagnostics Dashboard"):
                    st.warning("Use the metrics below to inspect if the deployment has successfully loaded your secrets.")
                    
                    # Environment Variables Info
                    st.markdown("### Environment Variables")
                    st.json({
                        "HF_TOKEN_set": "HF_TOKEN" in os.environ,
                        "HUGGINGFACEHUB_API_TOKEN_set": "HUGGINGFACEHUB_API_TOKEN" in os.environ,
                        "HUGGINGFACE_API_KEY_set": "HUGGINGFACE_API_KEY" in os.environ,
                        "HF_TOKEN_length": len(os.environ.get("HF_TOKEN", "")),
                        "HUGGINGFACEHUB_API_TOKEN_length": len(os.environ.get("HUGGINGFACEHUB_API_TOKEN", ""))
                    })
                    
                    # Streamlit Secrets Info
                    try:
                        st.markdown("### Streamlit Secrets")
                        st.json({
                            "available_secrets_keys": list(st.secrets.keys()) if hasattr(st, "secrets") else [],
                            "secrets_lengths": {k: len(str(st.secrets[k])) for k in st.secrets.keys()} if hasattr(st, "secrets") else {}
                        })
                    except Exception as secrets_err:
                        st.error(f"Error accessing Streamlit Secrets: {secrets_err}")

# ----------------- PAGE 2: HISTORY & LOGS -----------------
elif page == "📊 Database History & Logs":
    st.markdown("# 📊 Interaction History & Analytics")
    st.markdown("Below is the performance analysis and logs retrieved from SQLite database (`chatbot.db`).")

    try:
        df = fetch_logs()
        
        if df.empty:
            st.info("No chat logs found in the database yet. Go back to the Chat Assistant and ask a question!")
        else:
            # Metrics
            total_chats = len(df)
            total_tokens = df["total_tokens"].sum()
            total_cost = df["estimated_cost"].sum()
            avg_tokens = df["total_tokens"].mean()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Interactions", f"{total_chats}")
            with col2:
                st.metric("Total Tokens Transacted", f"{total_tokens:,}")
            with col3:
                st.metric("Accumulated Cost", f"${total_cost:.5f}")
            with col4:
                st.metric("Avg. Tokens/Chat", f"{avg_tokens:.1f}")

            st.markdown("---")
            
            # Action controls
            col_search, col_actions = st.columns([3, 1])
            with col_search:
                search_query = st.text_input("🔍 Search logs (by User Query or AI Response):", "")
            with col_actions:
                st.write("") # Spacer
                st.write("") # Spacer
                if st.button("🗑️ Clear History", use_container_width=True):
                    clear_logs()
                    st.success("Database logs cleared successfully!")
                    st.rerun()

            # Filter data if search input is provided
            if search_query:
                filtered_df = df[
                    df["user_query"].str.contains(search_query, case=False, na=False) |
                    df["ai_response"].str.contains(search_query, case=False, na=False)
                ]
            else:
                filtered_df = df

            # Show logs in a tabbed view or expanders for readability
            st.write(f"Showing {len(filtered_df)} of {total_chats} entries:")
            
            tab_table, tab_cards, tab_charts = st.tabs(["📋 Data Table", "🗂️ Detailed Cards", "📈 Token Usage Charts"])
            
            with tab_table:
                # Format dataframe for display
                display_df = filtered_df.copy()
                display_df["timestamp"] = pd.to_datetime(display_df["timestamp"])
                
                # Excel/CSV download option
                csv = display_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export Logs to CSV",
                    data=csv,
                    file_name=f"chatbot_history_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )
                
                st.dataframe(
                    display_df,
                    column_config={
                        "id": "ID",
                        "timestamp": "Timestamp",
                        "user_query": st.column_config.TextColumn("User Query", width="medium"),
                        "ai_response": st.column_config.TextColumn("AI Response", width="large"),
                        "input_tokens": "Input Tokens",
                        "output_tokens": "Output Tokens",
                        "total_tokens": "Total Tokens",
                        "estimated_cost": st.column_config.NumberColumn("Est. Cost", format="$%.5f"),
                        "model_name": "Model Used"
                    },
                    hide_index=True,
                    use_container_width=True
                )

            with tab_cards:
                for idx, row in filtered_df.iterrows():
                    with st.container():
                        st.markdown(f"### Chat Record #{row['id']} - `{row['timestamp']}`")
                        col_meta_1, col_meta_2, col_meta_3 = st.columns(3)
                        col_meta_1.write(f"**Tokens:** {row['total_tokens']} (In: {row['input_tokens']} | Out: {row['output_tokens']})")
                        col_meta_2.write(f"**Cost:** ${row['estimated_cost']:.6f}")
                        col_meta_3.write(f"**Model:** {row['model_name']}")
                        
                        st.markdown("**User Query:**")
                        st.info(row['user_query'])
                        st.markdown("**AI Response:**")
                        st.success(row['ai_response'])
                        st.markdown("---")

            with tab_charts:
                st.subheader("Tokens Transacted over Time")
                chart_df = df.copy()
                # Ensure correct ordering for chronological chart
                chart_df = chart_df.iloc[::-1]
                chart_df["timestamp"] = pd.to_datetime(chart_df["timestamp"])
                chart_df.set_index("timestamp", inplace=True)
                
                # Line chart of tokens
                st.line_chart(chart_df[["input_tokens", "output_tokens", "total_tokens"]])
                
                st.subheader("Cost Accumulation Curve")
                chart_df["cumulative_cost"] = chart_df["estimated_cost"].cumsum()
                st.area_chart(chart_df["cumulative_cost"])
                
    except Exception as e:
        st.error(f"Error fetching database logs: {str(e)}")
