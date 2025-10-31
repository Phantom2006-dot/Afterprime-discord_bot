# Credentials Required to Run Social Army Discord Bot

## Overview
The Social Army Discord bot now supports **LinkedIn, Instagram/Meta, and TikTok**. You'll need to obtain credentials from each platform and configure them in your Replit environment.

---

## 1. Discord Bot Credentials

### Where to Get Them
1. Go to https://discord.com/developers/applications
2. Create a "New Application" or select your existing bot
3. Go to the "Bot" section
4. Click "Reset Token" and copy the bot token
5. Enable these Privileged Gateway Intents:
   - SERVER MEMBERS INTENT
   - MESSAGE CONTENT INTENT

### Required Environment Variables
```
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_GUILD_ID=your_discord_server_id
ADMIN_ROLE_NAME=Admin
```

### Discord Server Setup
Create these roles (exact names):
- Recruit
- Soldier
- General
- Warlord

Create these channels:
- #social-army (for mission announcements)
- #audit-log (for tracking)

Get Role/Channel IDs (enable Developer Mode in Discord, right-click to copy ID):
```
RECRUIT_ROLE_ID=role_id_here
SOLDIER_ROLE_ID=role_id_here
GENERAL_ROLE_ID=role_id_here
WARLORD_ROLE_ID=role_id_here
MISSION_CHANNEL_ID=channel_id_here
AUDIT_CHANNEL_ID=channel_id_here
```

---

## 2. LinkedIn OAuth Credentials

### Where to Get Them
1. Go to https://www.linkedin.com/developers/apps
2. Create a new app or select existing
3. Add OAuth 2.0 redirect URL: `https://your-repl-url.repl.co/oauth/linkedin/callback`
4. Request these products:
   - "Sign In with LinkedIn"
   - "Share on LinkedIn"
5. Under "Auth" tab, copy Client ID and Client Secret

### Required Environment Variables
```
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
```

### Scopes Automatically Requested
- `w_member_social` (post on behalf of user)
- `r_liteprofile` (get user profile)
- `r_basicprofile` (basic profile info)

---

## 3. Meta (Facebook/Instagram) OAuth Credentials

### Where to Get Them
1. Go to https://developers.facebook.com/apps
2. Create a new app (choose "Business" type)
3. Add "Instagram Basic Display" and "Instagram Content Publishing" products
4. Under Settings → Basic, copy App ID and App Secret
5. Add OAuth redirect URI: `https://your-repl-url.repl.co/oauth/meta/callback`

### Required Environment Variables
```
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
```

### Important Notes
- Users MUST have Instagram Business accounts
- Instagram Business accounts must be linked to a Facebook Page
- Users will need to select which Instagram account to use during OAuth

### Scopes Automatically Requested
- `pages_manage_posts` (publish to pages)
- `pages_read_engagement` (read engagement metrics)
- `pages_show_list` (list connected pages)
- `instagram_basic` (basic Instagram access)
- `instagram_content_publish` (publish to Instagram)

---

## 4. TikTok OAuth Credentials

### Where to Get Them
1. Go to https://developers.tiktok.com/
2. Register as a developer
3. Create a new app
4. Add redirect URI: `https://your-repl-url.repl.co/oauth/tiktok/callback`
5. Request "Content Posting API" access (requires approval)
6. Copy Client Key and Client Secret

### Required Environment Variables
```
TIKTOK_CLIENT_KEY=your_tiktok_client_key
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret
```

### Important Notes
- TikTok Content Posting API requires approval from TikTok
- Video content must be provided as publicly accessible URLs
- Posting can take several minutes to process

### Scopes Automatically Requested
- `video.upload` (upload videos)
- `user.info.basic` (basic user info)

---

## 5. Bitly API Token (Optional but Recommended)

### Where to Get It
1. Sign up at https://bitly.com/
2. Go to Settings → API → Generate Access Token
3. Copy the access token

### Required Environment Variable
```
BITLY_ACCESS_TOKEN=your_bitly_token
```

### What It Enables
- Unique short URLs for each user/mission combination
- Click tracking for bonus points
- UTM parameter tracking for analytics

**If not provided**: The bot will still work, but URLs won't be shortened and click tracking will be disabled.

---

## 6. Encryption Key

### How to Generate
Run this command in the Replit Shell:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Required Environment Variable
```
ENCRYPTION_KEY=the_generated_key_here
```

### What It's Used For
- Encrypting OAuth access tokens in the database
- Encrypting refresh tokens
- Ensuring secure storage of sensitive credentials

---

## 7. Base URL (Auto-configured by Replit)

### Required Environment Variable
```
BASE_URL=https://your-repl-name.your-username.repl.co
```

**Note**: Replit usually sets this automatically. If not, you can find it in the Webview URL when you run your repl.

---

## 8. Optional Configuration

### Polling Intervals
Control how often the bot checks for engagement metrics:

```
METRICS_POLL_INTERVAL=3600    # Check platform metrics every hour (in seconds)
CLICKS_POLL_INTERVAL=300      # Check Bitly clicks every 5 minutes (in seconds)
```

---

## Complete .env Template

Copy this to your Replit Secrets or .env file and fill in all values:

```env
# Discord
DISCORD_BOT_TOKEN=
DISCORD_GUILD_ID=
ADMIN_ROLE_NAME=Admin
RECRUIT_ROLE_ID=
SOLDIER_ROLE_ID=
GENERAL_ROLE_ID=
WARLORD_ROLE_ID=
MISSION_CHANNEL_ID=
AUDIT_CHANNEL_ID=

# Base URL (usually auto-set by Replit)
BASE_URL=https://your-repl-name.your-username.repl.co

# LinkedIn
LINKEDIN_CLIENT_ID=
LINKEDIN_CLIENT_SECRET=

# Meta/Instagram
META_APP_ID=
META_APP_SECRET=

# TikTok
TIKTOK_CLIENT_KEY=
TIKTOK_CLIENT_SECRET=

# Bitly (optional)
BITLY_ACCESS_TOKEN=

# Security
ENCRYPTION_KEY=

# Database (auto-configured by Replit)
DATABASE_URL=

# Polling Intervals (optional, defaults shown)
METRICS_POLL_INTERVAL=3600
CLICKS_POLL_INTERVAL=300
```

---

## Next Steps

1. ✅ Obtain all credentials from the platforms above
2. ✅ Add all credentials to Replit Secrets
3. ✅ Create Discord roles and channels
4. ✅ Click "Run" to start the bot
5. ✅ Test `/connect` command for each platform
6. ✅ Test `/post` command with a test mission

---

## Testing Checklist

- [ ] Bot comes online in Discord
- [ ] `/connect` shows platform selection
- [ ] LinkedIn OAuth works
- [ ] Instagram/Meta OAuth works
- [ ] TikTok OAuth works
- [ ] Can create missions via admin commands
- [ ] Can post missions to each platform
- [ ] Engagement tracking updates scores
- [ ] Click tracking works (if Bitly configured)
- [ ] Roles update based on scores

---

## Support

If you encounter issues:
1. Check the Replit console logs for errors
2. Verify all credentials are correct
3. Ensure redirect URIs match exactly (including https://)
4. Confirm platform apps are approved/live
5. For Instagram: Ensure users have Business accounts

---

## Platform-Specific Gotchas

### LinkedIn
- App must be approved for production use
- Test with personal account first

### Instagram/Meta
- Users MUST have Instagram Business accounts
- Business accounts must be connected to Facebook Pages
- App must be in "Live" mode for general use

### TikTok
- Content Posting API requires manual approval from TikTok
- May take several days to get approved
- Test with developer account first

### Bitly
- Free tier has rate limits
- Consider upgrading if you have many users
