import requests
import json

API_KEY = "sk-fdbbc01319c74effbca6cb4c40215e10"   # <-- paste your key here

url = "https://api.deepseek.com/chat/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

payload = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "user", "content": "Hello, can you hear me?"}
    ]
}

response = requests.post(url, headers=headers, data=json.dumps(payload))

print("Status Code:", response.status_code)
print("Response:\n", response.text)
