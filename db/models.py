# db/models.py

from datetime import datetime
import os

from dotenv import load_dotenv
from sqlalchemy import (
    Boolean, Column, DateTime, Float,
    ForeignKey, Integer, String, Text, create_engine,text
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from pgvector.sqlalchemy import Vector

# --------------------------------------------------
# 1. Load environment variables from .env file
# --------------------------------------------------
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
# DATABASE_URL format: postgresql://user:password@host:port/dbname

# --------------------------------------------------
# 2. Engine — single connection point to PostgreSQL
# --------------------------------------------------
engine = create_engine(DATABASE_URL)

# --------------------------------------------------
# 3. Base — all models inherit from this
# --------------------------------------------------
Base = declarative_base()

# --------------------------------------------------
# 4. SessionLocal — factory that creates DB sessions
#    autocommit=False → you control when to commit
#    autoflush=False  → changes not sent until commit
# --------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --------------------------------------------------
# 5. Meeting table — stores raw transcript
# --------------------------------------------------
class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=True)
    raw_transcript = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # one meeting → many action items
    action_items = relationship("ActionItem", back_populates="meeting")
    # one meeting → many embedding chunks
    embeddings = relationship("MeetingEmbedding", back_populates="meeting")


# --------------------------------------------------
# 6. ActionItem table — stores extracted tasks
# --------------------------------------------------
class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    task = Column(Text, nullable=False)
    owner = Column(String, nullable=True)       # person responsible
    deadline = Column(String, nullable=True)    # storing as string eg "next Friday"
    priority = Column(String, nullable=False)   # High / Medium / Low
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    needs_review = Column(Boolean, default=False)     # True if confidence < 0.7

    meeting = relationship("Meeting", back_populates="action_items")


# --------------------------------------------------
# 7. MeetingEmbedding table — stores vector chunks
#    Vector(1536) = OpenAI/Anthropic embedding size
#    Used for semantic search across past meetings
# --------------------------------------------------
class MeetingEmbedding(Base):
    __tablename__ = "meeting_embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(1536))

    meeting = relationship("Meeting", back_populates="embeddings")


# --------------------------------------------------
# 8. init_db() — call once at app startup
#    Creates all tables if they don't exist
# --------------------------------------------------
def init_db():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)


# --------------------------------------------------
# 9. get_db() — dependency used in FastAPI routes
#    yields session → route uses it → session closed
# --------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()