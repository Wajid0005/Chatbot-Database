import os
from dotenv import load_dotenv

print("Running Qwen File")
load_dotenv()

# Inject Streamlit secrets into environment variables if running in Streamlit
try:
    import streamlit as st
    # Case-insensitive scan of all secrets to find matching token names
    for key in st.secrets.keys():
        upper_key = key.upper()
        if upper_key in ["HUGGINGFACEHUB_API_TOKEN", "HF_TOKEN", "HUGGINGFACE_API_KEY", "HF_API_KEY"]:
            token = st.secrets[key]
            os.environ["HUGGINGFACEHUB_API_TOKEN"] = token
            os.environ["HF_TOKEN"] = token
            os.environ["HUGGINGFACE_API_KEY"] = token
except Exception as e:
    print(f"Error reading secrets: {e}")

# Synchronize local/system environment variables (case-insensitive check)
for env_key in list(os.environ.keys()):
    upper_key = env_key.upper()
    if upper_key in ["HUGGINGFACEHUB_API_TOKEN", "HF_TOKEN", "HUGGINGFACE_API_KEY", "HF_API_KEY"]:
        token = os.environ[env_key]
        os.environ["HUGGINGFACEHUB_API_TOKEN"] = token
        os.environ["HF_TOKEN"] = token
        os.environ["HUGGINGFACE_API_KEY"] = token

from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

api_token = os.environ.get("HF_TOKEN")

llm = HuggingFaceEndpoint(
    repo_id="Qwen/Qwen2.5-7B-Instruct",
    task="text-generation",
    huggingfacehub_api_token=api_token
)

model = ChatHuggingFace(llm=llm)
