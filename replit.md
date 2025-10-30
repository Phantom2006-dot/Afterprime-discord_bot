# Social Army Discord Bot

## Overview
A Discord bot that gamifies brand amplification through social media missions. Users connect their LinkedIn accounts, post brand missions with one click, and earn points that contribute to monthly leaderboards and role progression.

## Recent Changes
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
- **OAuth**: LinkedIn OAuth 2.0
- **Security**: Fernet encryption for tokens

### File Structure
```
.
├── bot.py              # Main Discord bot with slash commands
├── oauth_server.py     # FastAPI OAuth callback server
├── database.py         # SQLAlchemy models and database init
├── encryption.py       # Token encryption utilities
├── config.py           # Configuration management
├── start.py           # Startup script (runs bot + OAuth server)
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variable template
└── README.md          # Complete setup instructions
```

### Database Schema
- **users**: Discord user info, scores, and current rank
- **social_accounts**: Connected social media accounts with encrypted tokens
- **missions**: Admin-created missions with content and metadata
- **posts**: User posts to missions with engagement metrics

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
