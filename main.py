from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from deep_translator import GoogleTranslator, single_detection
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# HARDCORE CONFIGURATION

load_dotenv()
# -----------------------------------------------------------------------------

MODEL_NAME = "openai/gpt-3.5-turbo"  # You can also try "openai/gpt-4o-mini"

# -----------------------------------------------------------------------------
# FASTAPI APP SETUP
# -----------------------------------------------------------------------------
app = FastAPI(title="HAMASA MEDIA AI Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# DATABASE SETUP (SQLite)
# -----------------------------------------------------------------------------
DATABASE_URL = "sqlite:///./chat_history.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    user_message = Column(String)
    ai_reply = Column(String)
    language_detected = Column(String)


Base.metadata.create_all(bind=engine)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL")

if not OPENROUTER_API_KEY or not OPENROUTER_BASE_URL:
    raise ValueError("❌ Missing OpenRouter API credentials in .env file!")

# -----------------------------------------------------------------------------
# OPENROUTER CLIENT
# -----------------------------------------------------------------------------
client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY
)

# -----------------------------------------------------------------------------
# REQUEST SCHEMA
# -----------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str


# -----------------------------------------------------------------------------
# ROOT ROUTE
# -----------------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "✅ HAMASA AI Backend (OpenRouter) is running successfully!"}


# -----------------------------------------------------------------------------
# CHAT ENDPOINT
# -----------------------------------------------------------------------------
@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    user_message = request.message

    # --- Detect language ---
    try:
        user_lang = single_detection(user_message, api_key=None)
    except Exception:
        user_lang = "en"

    # --- Translate to English if Swahili ---
    if user_lang == "sw":
        translated_text = GoogleTranslator(source="sw", target="en").translate(user_message)
    else:
        translated_text = user_message

    # --- Send request to OpenRouter ---
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant knowledgeable about Tanzanian media laws, press freedom, and survey insights."
                },
                {"role": "user", "content": translated_text}
            ],
            timeout=40
        )
        ai_reply = response.choices[0].message.content
    except Exception as e:
        return {"error": f"⚠️ OpenRouter request failed: {str(e)}"}

    # --- Save to SQLite database ---
    try:
        db = SessionLocal()
        chat_entry = Chat(
            user_message=user_message,
            ai_reply=ai_reply,
            language_detected=user_lang
        )
        db.add(chat_entry)
        db.commit()
        db.close()
    except Exception as e:
        print("⚠️ DB Error:", e)

    # --- Translate back to Swahili if needed ---
    if user_lang == "sw":
        try:
            ai_reply = GoogleTranslator(source="en", target="sw").translate(ai_reply)
        except Exception:
            pass

    return {
        "reply": ai_reply,
        "language_detected": user_lang
    }
