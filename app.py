from model import model
from token_counter import count_token
from database import save_chat

question = input("Ask: ")

response = model.invoke(question)

answer = response.content

input_tokens = count_token(question)
output_tokens = count_token(answer)

total_tokens = input_tokens + output_tokens

cost = 0

save_chat(
    question,
    answer,
    input_tokens,
    output_tokens,
    total_tokens,
    cost,
    "Qwen/Qwen2.5-7B-Instruct"
)

print(answer)