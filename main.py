from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from deep_translator import GoogleTranslator, single_detection
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import Optional
from media_knowledge import MEDIA_LAWS_KNOWLEDGE, JOURNALISM_ETHICS, MEDIA_MARKET_INSIGHTS
import json
import requests

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------
# FASTAPI APP
# ---------------------------------------------------------------------
app = FastAPI(
    title="HAMASA MEDIA AI Assistant",
    description="AI Assistant for Tanzanian media laws and press freedom",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------
# DEEPSEEK CONFIG
# ---------------------------------------------------------------------
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
client_available = bool(DEEPSEEK_API_KEY)
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

def deepseek_chat(system_prompt: str, user_content: str, temperature=0.7, max_tokens=500):
    if not client_available:
        return None, "DeepSeek API key missing"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        resp = requests.post(DEEPSEEK_URL, json=payload, headers=headers, timeout=30)
    except Exception as e:
        return None, f"Request error: {e}"

    if resp.status_code != 200:
        return None, f"DeepSeek API error {resp.status_code}: {resp.text}"

    try:
        body = resp.json()
        ai_text = body["choices"][0]["message"]["content"].strip()
        return ai_text, None
    except Exception as e:
        return None, f"Parsing error: {e}"

# ---------------------------------------------------------------------
# SYSTEM PROMPT
# ---------------------------------------------------------------------
MEDIA_SYSTEM_PROMPT = f"""
You are Hamasa AI, an assistant specialized in Tanzanian media laws, ethics, & market insights.

CORE KNOWLEDGE:
1. Tanzanian Media Laws: {json.dumps(MEDIA_LAWS_KNOWLEDGE['tanzania'], indent=2)}
2. Journalism Ethics: {json.dumps(JOURNALISM_ETHICS, indent=2)}
3. Market Insights: {json.dumps(MEDIA_MARKET_INSIGHTS, indent=2)}

Respond briefly, accurately, and professionally.
"""

# ---------------------------------------------------------------------
# SCHEMAS
# ---------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    category: Optional[str] = "general"

class ChatResponse(BaseModel):
    reply: str
    language_detected: str
    category: str

class MediaLawQuery(BaseModel):
    law_type: str = "general"
    question: str

# ---------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Hamasa Media AI running",
        "deepseek": "connected" if client_available else "missing_api_key",
        "time": datetime.utcnow()
    }

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Detect language
    try:
        lang = single_detection(user_message)
    except:
        lang = "en"

    # Translate input
    translated = user_message
    if lang != "en":
        try:
            translated = GoogleTranslator(source=lang, target="en").translate(user_message)
        except:
            pass

    # Generate AI response
    prompt_text = f"Category: {request.category}\nQuestion: {translated}"
    ai_text, error = deepseek_chat(MEDIA_SYSTEM_PROMPT, prompt_text)

    if error:
        ai_text = "Sorry, I encountered an error. Please try again."

    # Translate back to user language
    final_reply = ai_text
    if lang != "en":
        try:
            final_reply = GoogleTranslator(source="en", target=lang).translate(ai_text)
        except:
            pass

    return ChatResponse(
        reply=final_reply,
        language_detected=lang,
        category=request.category
    )

# ---------------------------------------------------------------------
# MEDIA LAWS ENDPOINT
# ---------------------------------------------------------------------

@app.post("/media/laws")
def media_laws_query(query: MediaLawQuery):
    law_data = MEDIA_LAWS_KNOWLEDGE['tanzania']

    if query.law_type in law_data:
        specific = law_data[query.law_type]
        context = f"""
        Law: {specific['title']}
        Key Points: {', '.join(specific['key_points'])}
        Question: {query.question}
        """
    else:
        context = f"General Tanzanian media laws. Question: {query.question}"

    ai_text, error = deepseek_chat(MEDIA_SYSTEM_PROMPT, context)

    if error:
        ai_text = "General Tanzanian media laws include: Media Services Act 2016, Access to Information Act 2016, Cybercrimes Act 2015."

    return {"reply": ai_text, "law_type": query.law_type}

# ---------------------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "deepseek": "connected" if client_available else "missing_key",
        "timestamp": datetime.utcnow()
    }

# ---------------------------------------------------------------------
# OPTIONAL WHATSAPP WEBHOOK
# ---------------------------------------------------------------------
D360_API_KEY = os.getenv("D360_API_KEY")

def send_whatsapp_message(to_number: str, text: str):
    if not D360_API_KEY:
        print("No WhatsApp API key configured")
        return

    url = "https://waba.360dialog.io/v1/messages"
    headers = {
        "D360-API-KEY": D360_API_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "to": to_number,
        "type": "text",
        "text": {"body": text}
    }

    try:
        requests.post(url, headers=headers, json=body)
    except Exception as e:
        print("WhatsApp sending error:", e)

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(payload: dict):
    print("Incoming WhatsApp:", payload)

    if "messages" not in payload:
        return {"status": "ignored"}

    for msg in payload["messages"]:
        if msg.get("from") and msg.get("text"):
            user_number = msg["from"]
            user_message = msg["text"]["body"]

            # Use chat endpoint
            req = ChatRequest(message=user_message, category="general")
            res = chat_endpoint(req)

            # Send back
            send_whatsapp_message(user_number, res.reply)

    return {"status": "processed"}

# ---------------------------------------------------------------------
# LOCAL DEV
# ---------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
