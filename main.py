from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from deep_translator import GoogleTranslator, single_detection
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import List, Optional
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
    description="AI Assistant specialized in Tanzanian media laws and press freedom",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------
# DATABASE SETUP
# ---------------------------------------------------------------------
DATABASE_URL = "sqlite:///./hamasa_media.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    user_message = Column(Text)
    ai_reply = Column(Text)
    language_detected = Column(String(10))
    category = Column(String(50), default="general")
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------------------
# DEEPSEEK CLIENT (Environment Variables)
# ---------------------------------------------------------------------
# Put your DeepSeek API key here or in .env as DEEPSEEK_API_KEY
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY") or "sk-fdbbc01319c74effbca6cb4c40215e10"

# If no key provided, we fall back to demo mode (client_available False)
client_available = bool(DEEPSEEK_API_KEY)

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

# Helper to call DeepSeek API
def deepseek_chat(system_prompt: str, user_content: str, temperature: float = 0.7, max_tokens: int = 500):
    if not client_available:
        return None, "DeepSeek API key not configured. Running in demo mode."

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
        # return the raw text as an error message
        return None, f"DeepSeek API error {resp.status_code}: {resp.text}"

    try:
        body = resp.json()
        # DeepSeek returns structure similar to OpenAI: choices[0].message.content
        ai_text = body.get("choices", [])[0].get("message", {}).get("content", "").strip()
        return ai_text, None
    except Exception as e:
        return None, f"Response parsing error: {e}"

# Media-specific system prompt
MEDIA_SYSTEM_PROMPT = f"""
You are Hamasa AI, a specialized assistant for Hamasa Media focusing on Tanzanian and East African media landscape.

CORE KNOWLEDGE AREAS:
1. Tanzanian Media Laws: {json.dumps(MEDIA_LAWS_KNOWLEDGE['tanzania'], indent=2)}
2. Journalism Ethics: {json.dumps(JOURNALISM_ETHICS, indent=2)}
3. Market Insights: {json.dumps(MEDIA_MARKET_INSIGHTS, indent=2)}

GUIDELINES:
- Provide accurate, practical advice tailored to media professionals
- Cite specific laws and regulations when relevant
- Offer actionable recommendations
- Be informative yet conversational
- Focus on Tanzanian and East African context
- Acknowledge when you don't know something

Always prioritize accuracy and relevance to the Tanzanian media context.

MAKE SURE YOU ANSWER SHORTLY AND PRECISELY. 
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

class ChatHistoryItem(BaseModel):
    id: int
    user_message: str
    ai_reply: str
    language_detected: str
    category: str
    created_at: datetime

    class Config:
        from_attributes = True

# ---------------------------------------------------------------------
# ROOT ENDPOINT
# ---------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "message": "Hamasa Media AI Assistant backend is running",
        "version": "1.0.0",
        "status": "healthy" if client_available else "demo_mode_no_deepseek_key",
        "features": ["media-law-analysis", "multilingual-support", "chat-history"]
    }

# ---------------------------------------------------------------------
# CHAT ENDPOINT
# ---------------------------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    user_message = request.message.strip()
    category = request.category

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Detect language
    try:
        user_lang = single_detection(user_message, api_key=None)
    except Exception:
        user_lang = "en"

    # If DeepSeek client is not available (no API key), return demo response
    if not client_available:
        demo_responses = {
            "general": "I'm currently in demo mode. Please add your DeepSeek API key to enable full AI capabilities.",
            "laws": "Demo: Tanzanian media laws include the Media Services Act of 2016. Add API key for detailed analysis.",
            "ethics": "Demo: Journalistic ethics in Tanzania emphasize accuracy and fairness. Add API key for comprehensive guidance.",
            "strategy": "Demo: Media strategy involves audience analysis and content planning. Add API key for personalized advice."
        }
        ai_reply = demo_responses.get(category, demo_responses["general"])
    else:
        # Translate to English if needed for better AI understanding
        if user_lang != "en":
            try:
                translated_text = GoogleTranslator(source=user_lang, target="en").translate(user_message)
            except Exception as e:
                print(f"Translation error: {e}")
                translated_text = user_message
        else:
            translated_text = user_message

        # Prepare prompt and call DeepSeek
        prompt_content = f"Category: {category}\nQuestion: {translated_text}"
        ai_reply_text, error = deepseek_chat(MEDIA_SYSTEM_PROMPT, prompt_content, temperature=0.7, max_tokens=500)

        if error:
            print(f"DeepSeek Error: {error}")
            ai_reply = "I apologize, but I'm currently experiencing technical difficulties. Please try again in a moment."
        else:
            ai_reply = ai_reply_text or ""

    # Save to database
    try:
        chat_entry = Chat(
            user_message=user_message,
            ai_reply=ai_reply,
            language_detected=user_lang,
            category=category
        )
        db.add(chat_entry)
        db.commit()
        db.refresh(chat_entry)
    except Exception as e:
        print(f"Database Error: {e}")
        db.rollback()

    # Translate reply back to user's language if needed
    final_reply = ai_reply
    if user_lang != "en" and client_available:  # Only translate if we have real AI responses
        try:
            final_reply = GoogleTranslator(source="en", target=user_lang).translate(ai_reply)
        except Exception as e:
            print(f"Reply translation error: {e}")

    return ChatResponse(
        reply=final_reply,
        language_detected=user_lang,
        category=category
    )

# ---------------------------------------------------------------------
# CHAT HISTORY ENDPOINTS
# ---------------------------------------------------------------------
# Add specific media queries
class MediaLawQuery(BaseModel):
    law_type: str = "general"
    question: str

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(payload: dict, db: Session = Depends(get_db)):
    print("Incoming WhatsApp:", payload)

    if "messages" not in payload:
        return {"status": "ignored"}

    for msg in payload["messages"]:
        if msg.get("from") and msg.get("text"):
            user_number = msg["from"]
            user_message = msg["text"]["body"]

            # Use your existing chat logic
            req = ChatRequest(message=user_message, category="general")
            res = chat_endpoint(req, db)

            # Send reply back to WhatsApp
            send_whatsapp_message(user_number, res.reply)

    return {"status": "processed"}

@app.post("/media/laws")
def media_laws_query(query: MediaLawQuery):
    """Specialized endpoint for media law queries"""
    law_data = MEDIA_LAWS_KNOWLEDGE['tanzania']
    
    if query.law_type in law_data:
        specific_law = law_data[query.law_type]
        context = f"""
        Relevant Law: {specific_law['title']}
        Key Points: {', '.join(specific_law['key_points'])}
        Impact: {specific_law.get('impact', 'N/A')}
        
        User Question: {query.question}
        """
    else:
        context = f"General Tanzanian Media Laws context. User Question: {query.question}"
    
    if not client_available:
        reply = f"I can provide general information about Tanzanian media laws. Key laws include: Media Services Act 2016, Access to Information Act 2016, and Cybercrimes Act 2015. (Demo mode)"
    else:
        ai_text, error = deepseek_chat(MEDIA_SYSTEM_PROMPT, context)
        if error:
            print(f"DeepSeek Error: {error}")
            reply = f"I can provide general information about Tanzanian media laws. Key laws include: Media Services Act 2016, Access to Information Act 2016, and Cybercrimes Act 2015."
        else:
            reply = ai_text or ""
    
    return {"reply": reply, "law_type": query.law_type}

# Add analytics endpoint
@app.get("/analytics/usage")
def get_usage_analytics(db: Session = Depends(get_db)):
    """Get usage analytics for the assistant"""
    from sqlalchemy import func, Date
    
    # Total chats
    total_chats = db.query(func.count(Chat.id)).scalar()
    
    # Chats by language
    chats_by_lang = db.query(
        Chat.language_detected, 
        func.count(Chat.id)
    ).group_by(Chat.language_detected).all()
    
    # Chats by category
    chats_by_category = db.query(
        Chat.category,
        func.count(Chat.id)
    ).group_by(Chat.category).all()
    
    # Recent activity (last 7 days)
    recent_activity = db.query(
        func.cast(Chat.created_at, Date).label('date'),
        func.count(Chat.id)
    ).group_by('date').order_by('date').limit(7).all()
    
    return {
        "total_chats": total_chats,
        "language_breakdown": dict(chats_by_lang),
        "category_breakdown": dict(chats_by_category),
        "recent_activity": [{"date": str(ra[0]), "count": ra[1]} for ra in recent_activity]
    }


@app.get("/chat/history", response_model=List[ChatHistoryItem])
def get_chat_history(limit: int = 20, db: Session = Depends(get_db)):
    try:
        chats = db.query(Chat).order_by(Chat.created_at.desc()).limit(limit).all()
        return chats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving chat history: {str(e)}")

@app.get("/chat/history/{chat_id}", response_model=ChatHistoryItem)
def get_chat_by_id(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

@app.delete("/chat/history/{chat_id}")
def delete_chat(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    try:
        db.delete(chat)
        db.commit()
        return {"message": "Chat deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting chat: {str(e)}")

# ---------------------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------------------
@app.get("/health")
def health_check():
    deepseek_status = "connected" if client_available else "no_deepseek_key"
    return {
        "status": "healthy", 
        "deepseek": deepseek_status,
        "timestamp": datetime.utcnow()
    }

# ---------------------------------------------------------
# WHATSAPP (360DIALOG) INTEGRATION
# ---------------------------------------------------------

D360_API_KEY = os.getenv("D360_API_KEY")
WHATSAPP_SENDER = os.getenv("WHATSAPP_SENDER")

def send_whatsapp_message(to_number: str, text: str):
    """Send message back to user using 360Dialog"""
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
        response = requests.post(url, headers=headers, json=body)
        print("WhatsApp send response:", response.text)
    except Exception as e:
        print("Error sending WhatsApp message:", e)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
