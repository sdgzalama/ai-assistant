from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from googletrans import Translator
from deep_translator import GoogleTranslator, single_detection
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------
# FASTAPI APP
# ---------------------------------------------------------------------
app = FastAPI(title="HAMASA MEDIA AI Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------
# DATABASE (SQLite)
# ---------------------------------------------------------------------
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

# ---------------------------------------------------------------------
# OPENAI CLIENT (HARDCODED API KEY)
# ---------------------------------------------------------------------
client = OpenAI(
    api_key="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"
)

translator = Translator()

# ---------------------------------------------------------------------
# SCHEMAS
# ---------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str

# ---------------------------------------------------------------------
# ROOT
# ---------------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Hamasa Media AI Assistant backend is running"}

# ---------------------------------------------------------------------
# CHAT ENDPOINT
# ---------------------------------------------------------------------
@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    user_message = request.message.strip()

    # Detect language
    try:
        user_lang = single_detection(user_message, api_key=None)
    except Exception:
        user_lang = "en"

    # Translate to English if needed
    if user_lang == "sw":
        translated_text = GoogleTranslator(source="sw", target="en").translate(user_message)
    else:
        translated_text = user_message

    # Send to OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # change to gpt-3.5-turbo if needed
            messages=[
                {"role": "system", "content": "You are a helpful assistant knowledgeable about Tanzanian media laws, press freedom, and survey insights."},
                {"role": "user", "content": translated_text}
            ]
        )
        ai_reply = response.choices[0].message.content.strip()
    except Exception as e:
        print("⚠️ OpenAI Error:", e)
        ai_reply = "Sorry, I couldn’t connect to the AI service."

    # Save to DB
    try:
        db = SessionLocal()
        chat_entry = Chat(user_message=user_message, ai_reply=ai_reply, language_detected=user_lang)
        db.add(chat_entry)
        db.commit()
        db.close()
    except Exception as e:
        print("⚠️ Database Error:", e)

    # Translate reply to Swahili if user used Swahili
    if user_lang == "sw":
        try:
            ai_reply = GoogleTranslator(source="en", target="sw").translate(ai_reply)
        except Exception:
            pass

    return {"reply": ai_reply, "language_detected": user_lang}
