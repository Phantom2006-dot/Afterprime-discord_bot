# Social Army Discord Bot - Setup Guide

## Simplified Reaction-Based Scoring System

This bot has been simplified to focus on reaction-based scoring in Discord. All complex OAuth integrations and external platform posting features have been removed.

## Features

### ✅ Core Functionality
- Simple submission channel where users post social media links or screenshots
- Judges score submissions using emoji reactions
- Monthly leaderboard with automatic reset
- Points are awarded based on emoji reactions from judges

### 🎯 Emoji Point System

**Effort:**
- ✍️ 1 point
- 🎨 3 points
- 🎬 5 points
- 🎞️ 8 points

**Creativity:**
- 💡 2 points
- 🤯 4 points

**Reach:**
- 📊 2 points
- 🔥 4 points
- 🚀 8 points

**Consistency:**
- 🧡 2 points
- 💪 3 points

**Bonus (Owner Only):**
- 🏅 5 points
- 👑 10 points

## Setup Instructions

### 1. Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application or select an existing one
3. Go to the "Bot" section
4. Enable these Privileged Gateway Intents:
   - Server Members Intent
   - Message Content Intent
5. Copy your bot token (you'll need this for step 2)
6. Go to OAuth2 > URL Generator
7. Select scopes: `bot`, `applications.commands`
8. Select permissions:
   - Read Messages/View Channels
   - Send Messages
   - Manage Messages (to remove invalid reactions)
   - Read Message History
   - Add Reactions
   - Use Slash Commands
9. Copy the generated URL and invite the bot to your server

### 2. Environment Variables

Set these in Replit Secrets (or .env file):

**Required:**
```bash
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=your_server_id
SOCIAL_ARMY_CHANNEL_ID=channel_id_for_submissions
```

**Optional:**
```bash
ADMIN_ROLE_NAME=Admin
SOCIAL_ARMY_JUDGE_ROLE_NAME=Social Army Judge
SOCIAL_ARMY_ELITE_ROLE_NAME=Social Army Elite
LEADERBOARD_SIZE=10
```

### 3. Discord Server Setup

1. Create a channel called `#social-army` (or any name you prefer)
2. Get the channel ID (enable Developer Mode in Discord settings, right-click channel > Copy ID)
3. Create a role called "Social Army Judge" for users who can score submissions
4. Create a role called "Social Army Elite" for top monthly performers (optional)
5. Get the server/guild ID (right-click server name > Copy ID)

### 4. Run the Bot

The bot will automatically start when you run the project. You can also run it manually:

```bash
python start.py
```

## Bot Commands

### User Commands
- `/social-leaderboard` - View the monthly leaderboard
- `/social-stats [@user]` - View statistics for yourself or another user
- `/social-config` - View current bot configuration

### Admin Commands
- `/social-reset` - Reset monthly scores and announce winners
- `/social-export [limit]` - Export top users to a text file

## How It Works

1. **Submission**: Users post social media links or screenshots in the designated Social Army channel
2. **Judging**: Users with the "Social Army Judge" role react to posts with scoring emojis
3. **Scoring**: The bot automatically tracks points when judges add/remove reactions
4. **Leaderboard**: Monthly leaderboard shows top contributors
5. **Reset**: At the end of each month, an admin can reset scores and announce winners

## Rules

- Only users with "Social Army Judge" role can score posts
- Only the server owner can use bonus emojis (🏅 👑)
- Maximum 1 submission per user per day (enforced manually)
- Users must tag @afterprime on their actual social platform posts
- Deleting a message removes all associated points

## Database

The bot uses a PostgreSQL database with two simple tables:
- `social_scores` - Monthly point totals per user
- `social_message_scores` - Individual reaction scores

## Troubleshooting

### Bot Not Responding
1. Check that the bot is online in your server
2. Verify `DISCORD_BOT_TOKEN` is correct
3. Ensure bot has proper permissions
4. Run `/social-config` to verify configuration

### Reactions Not Working
1. Ensure you have the "Social Army Judge" role
2. Check that you're reacting in the correct channel
3. Verify the emoji is in the scoring system
4. For bonus emojis, check that you're the server owner

## Support

For issues or questions, check the bot logs in the console output.
