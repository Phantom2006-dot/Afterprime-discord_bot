# Social Army Discord Bot

A Discord bot that gamifies brand amplification through social media mission posting, OAuth integration, automated scoring, and monthly leaderboards.

## Features

- **Discord Slash Commands**: `/connect`, `/missions`, `/post`, `/score`, `/leaderboard`, `/rolesync`
- **Admin Commands**: `/mission new`, `/mission close`
- **LinkedIn Integration**: OAuth authentication and automated posting
- **Scoring System**: Points for publishing (+10), on-time bonus (+5)
- **Role-based Progression**: Recruit → Soldier → General → Warlord
- **Monthly Leaderboards**: Track top performers

## Prerequisites

- Python 3.11+
- PostgreSQL database
- Discord Bot Token
- LinkedIn OAuth credentials

## Setup Instructions

### 1. Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" tab and click "Add Bot"
4. Copy your bot token (you'll need this later)
5. Enable these Privileged Gateway Intents:
   - Server Members Intent
   - Message Content Intent
6. Go to OAuth2 → URL Generator
7. Select scopes: `bot`, `applications.commands`
8. Select bot permissions: `Manage Roles`, `Send Messages`, `Read Message History`
9. Copy the generated URL and use it to invite the bot to your server

### 2. Discord Server Setup

1. Create roles in your Discord server (or note existing role IDs):
   - Recruit (for 0-49 points)
   - Soldier (for 50-199 points)
   - General (for 200-499 points)
   - Warlord (for 500+ points)
   - Admin (for managing missions)
2. Right-click each role → Copy ID (enable Developer Mode in Discord settings if needed)
3. Create a channel for missions (e.g., `#social-army`) and copy its ID
4. Right-click your server → Copy ID (this is your Guild ID)

### 3. LinkedIn OAuth Setup

1. Go to [LinkedIn Developer Portal](https://www.linkedin.com/developers/apps)
2. Click "Create app"
3. Fill in your app details
4. Go to the "Auth" tab
5. Add OAuth 2.0 redirect URL: `http://localhost:8000/oauth/linkedin/callback`
   - For production, use your actual domain
6. Copy your Client ID and Client Secret
7. Go to "Products" tab and request access to "Share on LinkedIn"

### 4. Environment Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in your `.env` file with your credentials:
   ```env
   DISCORD_BOT_TOKEN=your_discord_bot_token
   DISCORD_GUILD_ID=your_server_id
   ADMIN_ROLE_NAME=Admin
   
   LINKEDIN_CLIENT_ID=your_linkedin_client_id
   LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
   OAUTH_REDIRECT_URI=http://localhost:8000/oauth/linkedin/callback
   
   DATABASE_URL=postgresql://user:password@host:port/database
   
   ENCRYPTION_KEY=generate_this_on_first_run
   
   RECRUIT_ROLE_ID=role_id_here
   SOLDIER_ROLE_ID=role_id_here
   GENERAL_ROLE_ID=role_id_here
   WARLORD_ROLE_ID=role_id_here
   
   MISSION_CHANNEL_ID=channel_id_here
   ```

3. Generate an encryption key:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
   Add this to your `.env` file as `ENCRYPTION_KEY`

### 5. Database Setup

The database will be automatically initialized when you first run the bot. Tables created:
- `users` - Discord user information and scores
- `social_accounts` - Connected social media accounts
- `missions` - Created missions
- `posts` - User posts to missions

### 6. Install Dependencies

```bash
pip install -r requirements.txt
```

### 7. Run the Bot

```bash
python start.py
```

This will start both:
- Discord bot (listening for commands)
- OAuth server on port 8000 (handling LinkedIn authentication)

## Usage

### For Users

1. **Connect LinkedIn**: `/connect`
   - Click the link to authorize LinkedIn
   - Once connected, you can post missions

2. **View Missions**: `/missions`
   - See all active missions

3. **Post a Mission**: `/post mission_id:1`
   - Preview the mission content
   - Click "Confirm & Post" to publish to LinkedIn
   - Earn points automatically!

4. **Check Score**: `/score`
   - View your total points, monthly score, and rank

5. **View Leaderboard**: `/leaderboard`
   - See the top 10 performers this month

6. **Sync Role**: `/rolesync`
   - Update your Discord role based on current score

### For Admins

1. **Create Mission**: `/mission action:new`
   - Fill in the modal with mission details
   - Mission will be posted to the designated channel

2. **Close Mission**: `/mission action:close mission_id:1`
   - Close an active mission

## Scoring System

- **Publish Success**: +10 points
- **On-time Bonus**: +5 points (within 24 hours of mission start)
- Future: Engagement tiers, click tracking

## Role Thresholds

- **Recruit**: 0-49 points
- **Soldier**: 50-199 points
- **General**: 200-499 points
- **Warlord**: 500+ points

## GitHub Integration & Deployment

### Push to GitHub

1. **Initialize Git Repository**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Social Army Discord bot"
   ```

2. **Create GitHub Repository**:
   - Go to [GitHub](https://github.com/new)
   - Create a new repository (public or private)
   - Don't initialize with README (we already have one)

3. **Push to GitHub**:
   ```bash
   git remote add origin https://github.com/yourusername/social-army-bot.git
   git branch -M main
   git push -u origin main
   ```

### Deploy to Production

#### Option 1: Replit Deployment
1. Keep the bot running on Replit
2. Update `OAUTH_REDIRECT_URI` in `.env` to use your Replit domain
3. Update LinkedIn OAuth redirect URLs to match

#### Option 2: VPS/Cloud Server
1. Clone the repository on your server
2. Set up environment variables
3. Use a process manager like `systemd` or `pm2`
4. Set up a reverse proxy (nginx) for the OAuth server
5. Use SSL certificates (Let's Encrypt)

#### Example systemd service:
```ini
[Unit]
Description=Social Army Discord Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/social-army-bot
ExecStart=/usr/bin/python3 start.py
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Option 3: Docker
Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "start.py"]
```

Build and run:
```bash
docker build -t social-army-bot .
docker run -d --env-file .env social-army-bot
```

## Future Features (Phase 2)

- Instagram Business integration
- TikTok integration
- Click tracking with short links (Bitly)
- Engagement-based scoring (reactions, views)
- Background workers for metrics polling
- Monthly leaderboard rollover
- Audit logging channel
- `/disconnect` command

## Troubleshooting

### Bot won't start
- Check your `DISCORD_BOT_TOKEN` is correct
- Ensure all required environment variables are set

### OAuth not working
- Verify LinkedIn redirect URI matches exactly
- Check LinkedIn app has "Share on LinkedIn" product enabled
- Ensure OAuth server is running on port 8000

### Commands not appearing
- Make sure bot has `applications.commands` scope
- Try `/sync` or restart the bot
- Check bot has proper permissions in the server

### Database errors
- Verify `DATABASE_URL` is correct
- Ensure PostgreSQL is running
- Check database user has proper permissions

## Support

For issues or questions, please open an issue on GitHub.

## License

MIT License
