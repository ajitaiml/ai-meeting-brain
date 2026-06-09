from datetime import datetime,timezone
import os

from dotenv import load_dotenv
from sqlalchemy import(
    Boolean,Column,DateTime,Float,
    ForeignKey,Integer,String,Text,create_engine,text,JSON
)

from sqlalchemy.orm import declarative_base,relationship,sessionmaker
from pgvector.sqlalchemy import Vector

# 1. Load Env variables from .env file
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

# 2. Engine - single connection point on PostgreSQL
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,        # test connection before using
    pool_recycle=300,          # recycle connections every 5 minutes
    connect_args={
        "sslmode": "require",
        "connect_timeout": 10
    }
)

# 3. Base - all models inherit from this
Base = declarative_base()

# 4. SessionLocal - factory that creates DB sessions
SessionLocal = sessionmaker(bind=engine)


# 5. Meeting Table - stores raw transcript
class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=True)
    raw_transcript = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    # --------------------------------------------------
    # store decisions and risks as JSON arrays
    # e.g. ["Decision 1", "Decision 2"]
    # --------------------------------------------------
    decisions = Column(JSON, nullable=True, default=list)
    risks = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    action_items = relationship("ActionItem", back_populates="meeting")
    embeddings = relationship("MeetingEmbedding", back_populates="meeting")
    
# 6. ActionItem Table - stores extracted tasks
class ActionItem(Base):
    __tablename__ = "action_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer,ForeignKey("meetings.id"), nullable=False)
    task = Column(String, nullable=True)
    owner = Column(String,nullable=True)
    deadline = Column(String, nullable=True)
    priority = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False)
    needs_review = Column(Boolean, default=False)
    
    meeting = relationship("Meeting",back_populates="action_items")
    
# 7. MeetingEmbedding Table - Stores Vector Chunks
class MeetingEmbedding(Base):
    __tablename__ = "meeting_embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(1536))

    meeting = relationship("Meeting", back_populates="embeddings")
    
# 8. init_db() - call once at app startup
#    Creates all tables if they don't exist
def init_db():
    with engine.connect() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    

# 9. get_db() - dependency used in FastAPI routes
#    yields session -> route uses it -> session closed
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close