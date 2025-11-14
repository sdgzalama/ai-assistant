

import os

# REPLACE with your NEW API key

from openai import OpenAI
import os

# REPLACE with your NEW API key
os.environ["OPENAI_API_KEY"] = "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"


client = OpenAI()

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "How are you?"}
        ]
    )

    print("API responded successfully!")
    print("Response:", response.choices[0].message.content)

except Exception as e:
    print("API key error or request failed:", e)
