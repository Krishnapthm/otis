from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="http://165.245.128.17:8081/v1",
)

response = client.chat.completions.create(
    model="mistralai/Mistral-7B-Instruct-v0.3",
    messages=[
        {"role": "user", "content": "Write a one-sentence bedtime story about a unicorn."}
    ],
)

print(response.choices[0].message.content)