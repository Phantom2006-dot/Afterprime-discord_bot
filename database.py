from sqlalchemy import create_engine, Column, Integer, String, DateTime, BigInteger, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import config

Base = declarative_base()

class SocialScore(Base):
    """Tracks monthly points per user"""
    __tablename__ = 'social_scores'
    
    id = Column(Integer, primary_key=True)
    discord_id = Column(String(50), nullable=False, index=True)
    discord_username = Column(String(100))
    month_key = Column(String(7), nullable=False, index=True)  # Format: YYYY-MM
    points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_user_month', 'discord_id', 'month_key'),
    )

class SocialMessageScore(Base):
    """Tracks individual reactions and their points"""
    __tablename__ = 'social_message_scores'
    
    id = Column(Integer, primary_key=True)
    message_id = Column(BigInteger, nullable=False, index=True)
    author_id = Column(String(50), nullable=False, index=True)
    judge_id = Column(String(50), nullable=False)
    emoji = Column(String(50), nullable=False)
    points = Column(Integer, nullable=False)
    month_key = Column(String(7), nullable=False, index=True)  # Format: YYYY-MM
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_message_judge_emoji', 'message_id', 'judge_id', 'emoji'),
    )

class SocialSubmission(Base):
    """Tracks daily submissions for rate limiting"""
    __tablename__ = 'social_submissions'
    
    id = Column(Integer, primary_key=True)
    discord_id = Column(String(50), nullable=False, index=True)
    date_key = Column(String(10), nullable=False, index=True)  # Format: YYYY-MM-DD
    message_id = Column(BigInteger, nullable=False)
    submission_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_user_date', 'discord_id', 'date_key'),
    )

def init_db():
    """Initialize the database schema"""
    engine = create_engine(config.DATABASE_URL)
    Base.metadata.create_all(engine)
    return engine

def get_session():
    """Get a database session"""
    engine = create_engine(config.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()
