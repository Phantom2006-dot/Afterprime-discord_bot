from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Float, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
import config

Base = declarative_base()

class PlatformType(str, enum.Enum):
    LINKEDIN = 'linkedin'
    META = 'meta'
    INSTAGRAM = 'instagram'
    TIKTOK = 'tiktok'
    TWITTER = 'twitter'

class MissionStatus(str, enum.Enum):
    DRAFT = 'draft'
    ACTIVE = 'active'
    CLOSED = 'closed'

class PostStatus(str, enum.Enum):
    PENDING = 'pending'
    PUBLISHED = 'published'
    FAILED = 'failed'

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
    scopes = Column(JSON)
    profile_data = Column(JSON)
    platform_metadata = Column(JSON)
    is_active = Column(Boolean, default=True)
    connected_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship('User', back_populates='social_accounts')

class Mission(Base):
    __tablename__ = 'missions'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    content = Column(Text, nullable=False)
    platforms = Column(JSON)
    media_urls = Column(JSON)
    target_url = Column(String(500))
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    status = Column(String(20), default='active')
    created_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    utm_params = Column(JSON)
    platform_configs = Column(JSON)
    
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
    bitly_id = Column(String(200))
    status = Column(String(20), default='pending')
    posted_at = Column(DateTime, default=datetime.utcnow)
    was_on_time = Column(Boolean, default=False)
    metrics = Column(JSON, default={})
    points_earned = Column(Integer, default=0)
    last_metrics_update = Column(DateTime)
    error_message = Column(Text)
    
    user = relationship('User', back_populates='posts')
    mission = relationship('Mission', back_populates='posts')
    engagement_snapshots = relationship('EngagementSnapshot', back_populates='post', cascade='all, delete-orphan')

class EngagementSnapshot(Base):
    __tablename__ = 'engagement_snapshots'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    snapshot_at = Column(DateTime, default=datetime.utcnow)
    clicks = Column(Integer, default=0)
    reactions = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    views = Column(Integer, default=0)
    platform_metrics = Column(JSON)
    points_awarded = Column(Integer, default=0)
    
    post = relationship('Post', back_populates='engagement_snapshots')

def init_db():
    engine = create_engine(config.DATABASE_URL)
    Base.metadata.create_all(engine)
    return engine

def get_session():
    engine = create_engine(config.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()
