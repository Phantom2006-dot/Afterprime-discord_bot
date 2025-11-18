# Social Army Discord Bot - Reaction-Based Scoring Edition

## Overview
A simplified Discord bot that gamifies social media engagement through reaction-based scoring. Judges award points to user submissions using emoji reactions, creating a competitive monthly leaderboard.

## Recent Changes
- **2025-11-18**: Major Simplification
  - Removed all OAuth integrations (LinkedIn, Meta, Instagram, TikTok)
  - Removed external platform posting functionality
  - Removed mission system and automated posting
  - Removed link shortener and engagement tracking workers
  - Removed token encryption system
  - Simplified to reaction-based scoring only
  - Reduced database to 2 simple tables
  - Implemented judge role system with emoji scoring
  - Added monthly reset functionality
  - Removed complex dependencies (FastAPI, cryptography, requests)

- **2025-10-31**: Multi-platform expansion (REMOVED)
- **2025-10-30**: Initial project setup

## Project Architecture

### Tech Stack
- **Language**: Python 3.12
- **Discord Framework**: discord.py 2.3.2
- **Database**: PostgreSQL (via SQLAlchemy ORM)
- **Environment**: python-dotenv

### File Structure
```
.
├── bot.py                  # Main Discord bot with reaction handlers and commands
├── database.py             # Simplified SQLAlchemy models (2 tables)
├── config.py               # Simple configuration
├── start.py                # Startup script (bot only)
├── requirements.txt        # Python dependencies
├── SETUP_GUIDE.md          # Setup instructions
└── replit.md               # This file
```

### Database Schema
- **social_scores**: Monthly point totals per user (discord_id, month_key, points)
- **social_message_scores**: Individual reaction scores (message_id, author_id, judge_id, emoji, points)

### Discord Commands

#### User Commands
- `/social-leaderboard` - View monthly leaderboard
- `/social-stats [@user]` - View user statistics
- `/social-config` - View configuration

#### Admin Commands
- `/social-reset` - Reset monthly scores and announce winners
- `/social-export [limit]` - Export top users to text file

### Emoji Scoring System
**Effort**: ✍️ (1), 🎨 (3), 🎬 (5), 🎞️ (8)
**Creativity**: 💡 (2), 🤯 (4)
**Reach**: 📊 (2), 🔥 (4), 🚀 (8)
**Consistency**: 🧡 (2), 💪 (3)
**Bonus**: 🏅 (5), 👑 (10) - Owner only

### How It Works
1. Users post social media links/screenshots in #social-army channel
2. Judges (users with "Social Army Judge" role) react with scoring emojis
3. Bot automatically adds/subtracts points when reactions are added/removed
4. Monthly leaderboard tracks top contributors
5. Admins can reset monthly and announce winners

## User Preferences
- Prefer simplified, maintainable code
- Focus on Discord-native functionality
- Remove external dependencies where possible

## Setup Status
- ✅ Python 3.12 installed
- ✅ Dependencies simplified and installed
- ✅ PostgreSQL database created and initialized
- ✅ Discord bot code complete with reaction handlers
- ⏳ Awaiting Discord bot token configuration

## Required Environment Variables
- `DISCORD_BOT_TOKEN` - Bot token from Discord Developer Portal
- `DISCORD_GUILD_ID` - Your Discord server ID
- `SOCIAL_ARMY_CHANNEL_ID` - Channel ID for submissions

## Optional Environment Variables
- `ADMIN_ROLE_NAME` - Admin role name (default: "Admin")
- `SOCIAL_ARMY_JUDGE_ROLE_NAME` - Judge role name (default: "Social Army Judge")
- `SOCIAL_ARMY_ELITE_ROLE_NAME` - Elite role name (default: "Social Army Elite")
- `LEADERBOARD_SIZE` - Number of users to show (default: 10)

## Next Steps
1. Set DISCORD_BOT_TOKEN in Replit Secrets
2. Set DISCORD_GUILD_ID and SOCIAL_ARMY_CHANNEL_ID
3. Create "Social Army Judge" role in Discord server
4. Test bot functionality
