from openai import OpenAI
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)
r = client.chat.completions.create(
    model="openai/gpt-3.5-turbo",
    messages=[{"role":"user","content":"Hello, are you working?"}]
)
print(r.choices[0].message.content)
