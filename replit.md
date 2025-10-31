# Social Army Discord Bot - Multi-Platform Edition

## Overview
A Discord bot that gamifies brand amplification through social media missions across LinkedIn, Instagram/Meta, and TikTok. Users connect their social accounts, post brand missions with one click, and earn points through engagement tracking that contribute to monthly leaderboards and role progression.

## Recent Changes
- **2025-10-31**: Multi-platform expansion
  - Added support for LinkedIn, Instagram/Meta, and TikTok
  - Implemented platform-specific OAuth flows and adapters
  - Created publishing service with platform-specific content transformation
  - Integrated Bitly link shortener for click tracking
  - Added engagement tracking workers for automated metrics polling
  - Enhanced database schema for multi-platform support
  - Updated all bot commands to support platform selection
  
- **2025-10-30**: Initial project setup
  - Created Discord bot with slash commands
  - Implemented LinkedIn OAuth integration
  - Set up PostgreSQL database with user, mission, and scoring tables
  - Built FastAPI OAuth callback server
  - Implemented point scoring and role progression system

## Project Architecture

### Tech Stack
- **Language**: Python 3.11
- **Discord Framework**: discord.py 2.3.2
- **Web Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL (via SQLAlchemy ORM)
- **OAuth**: Multi-platform OAuth 2.0 (LinkedIn, Meta, TikTok)
- **Security**: Fernet encryption for tokens
- **Link Tracking**: Bitly API integration
- **Background Workers**: AsyncIO-based engagement polling

### File Structure
```
.
├── bot.py                  # Main Discord bot with slash commands
├── oauth_server.py         # Multi-platform FastAPI OAuth server
├── database.py             # Enhanced SQLAlchemy models
├── encryption.py           # Token encryption utilities
├── config.py               # Multi-platform configuration
├── start.py                # Startup script (bot + OAuth + workers)
├── publishing_service.py   # Unified publishing service
├── engagement_workers.py   # Background metrics polling
├── link_shortener.py       # Bitly integration
├── platforms/              # Platform-specific adapters
│   ├── __init__.py
│   ├── base.py            # Base platform interface
│   ├── linkedin.py        # LinkedIn adapter
│   ├── meta.py            # Meta/Instagram adapter
│   └── tiktok.py          # TikTok adapter
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
├── SETUP_GUIDE.md         # Complete setup instructions
└── README.md              # Project documentation
```

### Database Schema
- **users**: Discord user info, scores, and current rank
- **social_accounts**: Multi-platform accounts with encrypted tokens, scopes, and metadata
- **missions**: Admin-created missions with multi-platform configs and media
- **posts**: User posts with platform-specific IDs, URLs, and short links
- **engagement_snapshots**: Historical engagement metrics polling data

### Discord Commands

#### User Commands
- `/connect` - Connect LinkedIn account via OAuth
- `/missions` - View active missions
- `/post` - Post a mission to LinkedIn
- `/score` - View personal score and rank
- `/leaderboard` - View top 10 performers
- `/rolesync` - Sync Discord role based on score

#### Admin Commands
- `/mission new` - Create new mission (opens modal)
- `/mission close` - Close an active mission

### Scoring System
- Publish success: +10 points
- On-time bonus (≤24h): +5 points
- Role thresholds:
  - Recruit: 0-49 points
  - Soldier: 50-199 points
  - General: 200-499 points
  - Warlord: 500+ points

## User Preferences
- No specific preferences set yet

## Setup Status
- ✅ Python 3.11 installed
- ✅ All dependencies installed
- ✅ Database schema created
- ✅ Discord bot code complete
- ✅ OAuth server ready
- ⏳ Awaiting user credentials (Discord bot token, LinkedIn OAuth, role IDs)

## Next Steps
1. User provides Discord bot token and server configuration
2. User sets up LinkedIn OAuth app and provides credentials
3. User creates Discord roles and channels, provides IDs
4. Test bot functionality
5. Deploy to production

## Phase 2 Features (Future)
- Instagram Business integration
- TikTok integration
- Bitly link shortening for click tracking
- Engagement-based scoring (reactions, views)
- Background workers for automated metrics polling
- Monthly leaderboard rollover and winner announcements
- Audit logging channel
- `/disconnect` command with token revocation
