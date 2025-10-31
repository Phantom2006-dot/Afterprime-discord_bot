# Social Army Discord Bot - Complete Setup Guide

## Overview
This bot gamifies brand amplification through social media missions across LinkedIn, Instagram/Meta, and TikTok with automatic engagement tracking and leaderboards.

## Features

### Phase 1 (Current)
- ✅ Multi-platform OAuth (LinkedIn, Instagram Business, TikTok)
- ✅ One-click mission posting
- ✅ Automatic engagement tracking
- ✅ Link shortening with click tracking (Bitly)
- ✅ Point-based scoring system
- ✅ Monthly leaderboards
- ✅ Role progression (Recruit → Soldier → General → Warlord)

## Prerequisites

1. **Discord Bot Setup**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a New Application
   - Go to "Bot" section and create a bot
   - Copy the Bot Token
   - Enable these Privileged Gateway Intents:
     - SERVER MEMBERS INTENT
     - MESSAGE CONTENT INTENT
   - Go to OAuth2 → URL Generator
   - Select scopes: `bot`, `applications.commands`
   - Select bot permissions: `Manage Roles`, `Send Messages`, `Embed Links`
   - Copy the generated URL and invite the bot to your server

2. **LinkedIn Developer App**
   - Go to [LinkedIn Developers](https://www.linkedin.com/developers/apps)
   - Create a new app
   - Add OAuth 2.0 redirect URL: `https://your-repl-url.repl.co/oauth/linkedin/callback`
   - Request these products:
     - Sign In with LinkedIn
     - Share on LinkedIn
   - Copy Client ID and Client Secret

3. **Meta (Facebook/Instagram) Developer App**
   - Go to [Meta for Developers](https://developers.facebook.com/apps)
   - Create a new app (Business type)
   - Add Instagram Basic Display and Instagram Content Publishing
   - Add OAuth redirect URI: `https://your-repl-url.repl.co/oauth/meta/callback`
   - Copy App ID and App Secret
   - Note: Users need Instagram Business accounts connected to Facebook Pages

4. **TikTok Developer App**
   - Go to [TikTok for Developers](https://developers.tiktok.com/)
   - Create a new app
   - Add redirect URI: `https://your-repl-url.repl.co/oauth/tiktok/callback`
   - Request Content Posting API access
   - Copy Client Key and Client Secret

5. **Bitly Account (Optional but Recommended)**
   - Sign up at [Bitly](https://bitly.com/)
   - Go to Settings → API → Generate Access Token
   - Copy the access token

## Installation Steps

### 1. Environment Variables Setup

Create a `.env` file or add these secrets in Replit:

```env
# Discord Bot
DISCORD_BOT_TOKEN=your_bot_token_from_discord_dev_portal
DISCORD_GUILD_ID=your_server_id
ADMIN_ROLE_NAME=Admin

# OAuth Base URL (Replit auto-sets this)
BASE_URL=https://your-repl-name.your-username.repl.co

# LinkedIn
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret

# Meta/Instagram
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret

# TikTok
TIKTOK_CLIENT_KEY=your_tiktok_client_key
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret

# Bitly
BITLY_ACCESS_TOKEN=your_bitly_token

# Encryption (generate with command below)
ENCRYPTION_KEY=generate_with_command_below

# Discord Roles (get IDs after creating roles)
RECRUIT_ROLE_ID=role_id
SOLDIER_ROLE_ID=role_id
GENERAL_ROLE_ID=role_id
WARLORD_ROLE_ID=role_id

# Discord Channels
MISSION_CHANNEL_ID=channel_id
AUDIT_CHANNEL_ID=channel_id
```

### 2. Generate Encryption Key

Run this command in the Replit Shell:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output and set it as `ENCRYPTION_KEY`.

### 3. Discord Server Setup

1. Create these roles in your Discord server (exact names):
   - Recruit
   - Soldier
   - General
   - Warlord

2. Create these channels:
   - #social-army (for mission announcements)
   - #audit-log (for admin tracking)

3. Get Role and Channel IDs:
   - Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
   - Right-click roles/channels and copy their IDs
   - Add them to your `.env` file

### 4. Database Initialization

The database will auto-initialize on first run. The PostgreSQL database is provided by Replit.

### 5. Start the Bot

Click the "Run" button in Replit. The bot will:
1. Initialize the database
2. Start the OAuth server on port 8000
3. Start the Discord bot
4. Start engagement tracking workers

## Usage Guide

### For Users

#### Connect Social Accounts
```
/connect
```
Select a platform to connect. You'll be redirected to authorize the app.

Supported platforms:
- LinkedIn
- Instagram (via Meta/Facebook)
- TikTok

#### View Active Missions
```
/missions
```
See all currently active missions with their details.

#### Post a Mission
```
/post mission_id:1 platform:linkedin
```
Select the mission and platform. You'll see a preview before posting.

#### Check Your Score
```
/score
```
View your total points, monthly score, and current rank.

#### View Leaderboard
```
/leaderboard
```
See the top 10 performers for the month.

#### Sync Your Role
```
/rolesync
```
Update your Discord role based on your current score.

### For Admins

#### Create a New Mission
```
/mission new
```
Opens a form to create a mission with:
- Title
- Description
- Content (what users will post)
- Platforms (linkedin, instagram, tiktok)
- Media URLs (comma-separated)
- Target URL (for link tracking)
- End date

#### Close a Mission
```
/mission close mission_id:1
```
Closes an active mission.

#### Edit a Mission
```
/mission edit mission_id:1
```
Modify an existing mission.

#### Audit a User
```
/audit user:@username
```
View all posts and activity for a specific user.

## Scoring System

### Base Points
- **Publish Success**: +10 points
- **On-Time Bonus** (≤24h): +5 points

### Click Tracking (via Bitly)
- **+1 point** per 10 unique clicks

### Engagement Tiers

**LinkedIn**
- 10 reactions: +5 points
- 30 reactions: +10 points
- 100 reactions: +20 points

**Instagram/Meta**
- 100 views: +5 points
- 500 views: +10 points
- 2000 views: +20 points

**TikTok**
- 100 views: +5 points
- 500 views: +10 points
- 2000 views: +20 points

### Top Clicker Bonuses (Monthly)
- 1st place: +25 points
- 2nd place: +15 points
- 3rd place: +10 points

## Role Thresholds
- **Recruit**: 0-49 points
- **Soldier**: 50-199 points
- **General**: 200-499 points
- **Warlord**: 500+ points

## Troubleshooting

### Bot Not Responding
1. Check that the bot is online in your server
2. Verify `DISCORD_BOT_TOKEN` is correct
3. Ensure bot has proper permissions
4. Run `/` to see if commands appear

### OAuth Failing
1. Verify redirect URIs match exactly (including https://)
2. Check that CLIENT_IDs and SECRETs are correct
3. Ensure apps are approved/live on each platform
4. For Instagram: Users must have Business accounts

### Posts Not Publishing
1. Check platform account is connected (`/connect`)
2. Verify token hasn't expired (reconnect if needed)
3. Check error messages in audit log
4. Ensure media URLs are publicly accessible

### Engagement Not Tracking
1. Verify Bitly token is valid
2. Check that posts have platform_post_ids
3. Look for errors in console logs
4. Ensure platform API access is granted

## Platform-Specific Notes

### LinkedIn
- Works with personal profiles
- Requires w_member_social scope
- Posts appear on user's feed
- Metrics update hourly

### Instagram
- Requires Instagram Business account
- Must be linked to a Facebook Page
- Only image posts supported (for now)
- User must select which IG account during OAuth

### TikTok
- Requires video content
- Content Posting API access needed (apply via developer portal)
- Videos must be publicly hosted
- Posting can take several minutes to process

## Security Best Practices

1. **Never commit `.env` file** - Already in .gitignore
2. **Tokens are encrypted** - Using Fernet encryption in database
3. **OAuth states validated** - Prevents CSRF attacks
4. **Audit logging** - All actions tracked in audit channel
5. **Rate limiting** - Built into engagement workers

## Support

For issues or questions:
1. Check the Replit console logs
2. Review the audit channel in Discord
3. Verify all credentials are correct
4. Ensure platform apps are approved/live

## Future Enhancements (Phase 2)

- Twitter/X integration
- Threads support
- Custom link shortener
- Automated monthly rollover
- Winner announcements
- Engagement predictions
- Content suggestions
