from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import config

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    discord_id = Column(String(50), unique=True, nullable=False, index=True)
    discord_username = Column(String(100))
    total_score = Column(Integer, default=0)
    monthly_score = Column(Integer, default=0)
    current_role = Column(String(50), default='Recruit')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    social_accounts = relationship('SocialAccount', back_populates='user', cascade='all, delete-orphan')
    posts = relationship('Post', back_populates='user', cascade='all, delete-orphan')

class SocialAccount(Base):
    __tablename__ = 'social_accounts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    platform = Column(String(50), nullable=False)
    platform_user_id = Column(String(200))
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expiry = Column(DateTime)
    profile_data = Column(JSON)
    connected_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship('User', back_populates='social_accounts')

class Mission(Base):
    __tablename__ = 'missions'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    content = Column(Text, nullable=False)
    platforms = Column(JSON)
    media_url = Column(String(500))
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    status = Column(String(20), default='active')
    created_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    utm_params = Column(JSON)
    
    posts = relationship('Post', back_populates='mission', cascade='all, delete-orphan')

class Post(Base):
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    mission_id = Column(Integer, ForeignKey('missions.id'), nullable=False)
    platform = Column(String(50), nullable=False)
    platform_post_id = Column(String(200))
    post_url = Column(String(500))
    short_url = Column(String(200))
    posted_at = Column(DateTime, default=datetime.utcnow)
    was_on_time = Column(Boolean, default=False)
    metrics = Column(JSON, default={})
    points_earned = Column(Integer, default=0)
    
    user = relationship('User', back_populates='posts')
    mission = relationship('Mission', back_populates='posts')

def init_db():
    engine = create_engine(config.DATABASE_URL)
    Base.metadata.create_all(engine)
    return engine

def get_session():
    engine = create_engine(config.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()
