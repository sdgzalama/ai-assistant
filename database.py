from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# SQLite database path
DATABASE_URL = "sqlite:///./chat_history.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Chat table model
class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    user_message = Column(Text)
    ai_reply = Column(Text)
    language_detected = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables automatically
Base.metadata.create_all(bind=engine)
