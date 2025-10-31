# Discord Bot Testing Guide

## ✅ Bot Status
Your bot **Afterprime_bot#3779** is now **ONLINE** and connected to Discord!

All 7 commands have been synced successfully.

---

## 🧪 Commands to Test

### 1. `/connect` - Connect Social Media Accounts
**Who can use:** All users

**How to test:**
1. In your Discord server, type `/connect`
2. You should see an embed with platform selection dropdown
3. Select a platform (LinkedIn, Instagram/Meta, or TikTok)
4. Click the "Connect" button that appears
5. Complete OAuth authorization in the browser
6. Return to Discord - you should now be connected

**Expected result:**
- Platform selection dropdown appears
- OAuth link opens in browser
- After authorizing, your account is linked
- Running `/connect` again shows your connected platforms with ✅

---

### 2. `/missions` - View Active Missions
**Who can use:** All users

**How to test:**
1. Type `/missions` in Discord
2. View the list of active missions

**Expected result:**
- If no missions exist: "No active missions right now. Check back soon!"
- If missions exist: Shows up to 5 missions with title, description, platforms, and end date

**Note:** You'll need to create missions first using the admin command (see `/mission new` below)

---

### 3. `/post` - Post a Mission to Social Media
**Who can use:** All users (who have connected accounts)

**How to test:**
1. First, make sure you have:
   - Connected at least one platform using `/connect`
   - An active mission exists (created by admin)
2. Type `/post` in Discord
3. Select a mission from the dropdown
4. Select which platform to post to
5. The bot will publish the mission to your social media

**Expected result:**
- Mission selection dropdown appears
- Platform selection appears (only shows your connected platforms)
- Success message confirms the post was published
- You earn points (+10 base, +5 if within 24h of mission start)
- Post appears on your selected social media platform

---

### 4. `/score` - Check Your Score
**Who can use:** All users

**How to test:**
1. Type `/score` in Discord
2. View your personal stats

**Expected result:**
Shows an embed with:
- Your total score
- Current rank (Recruit/Soldier/General/Warlord)
- Number of posts you've made
- Progress to next rank (if applicable)

---

### 5. `/leaderboard` - View Top Performers
**Who can use:** All users

**How to test:**
1. Type `/leaderboard` in Discord
2. View the rankings

**Expected result:**
- Shows top 10 users ranked by score
- Displays: Username, Total Score, Rank, Posts Count
- Shows a 🏆 trophy emoji next to the #1 user

---

### 6. `/rolesync` - Sync Your Discord Role
**Who can use:** All users

**How to test:**
1. Type `/rolesync` in Discord
2. Bot will update your Discord role based on your score

**Expected result:**
- Bot assigns you the correct role based on your score:
  - **Recruit**: 0-49 points
  - **Soldier**: 50-199 points
  - **General**: 200-499 points
  - **Warlord**: 500+ points
- Confirmation message shows your new role

---

### 7. `/mission` - Admin Commands (ADMIN ONLY)
**Who can use:** Users with the "Admin" role

This command has two subcommands:

#### `/mission new` - Create a New Mission
**How to test:**
1. Type `/mission new` in Discord
2. A modal form will appear asking for:
   - Title
   - Description
   - Platforms (comma-separated: linkedin, meta, tiktok)
   - Media URL (optional image/video)
   - End date (YYYY-MM-DD format, optional)
3. Fill out the form and submit
4. Mission is created and announced in the mission channel

**Expected result:**
- Modal form appears
- After submission, mission is created
- Announcement posted in the mission channel (if configured)
- Users can now see this mission in `/missions` and `/post`

#### `/mission close <mission_id>` - Close a Mission
**How to test:**
1. Type `/mission close` and provide a mission ID number
2. The mission will be closed

**Expected result:**
- Mission status changes to "closed"
- Users can no longer post to this mission
- Confirmation message appears

---

## 🎯 Complete Testing Flow

Here's a step-by-step test of the full user journey:

1. **Admin creates a mission**
   - `/mission new`
   - Fill in: "Test Mission", "Share this post!", "linkedin,meta", no media, no end date
   - Verify announcement appears

2. **User connects account**
   - `/connect`
   - Select LinkedIn (or Meta/TikTok)
   - Complete OAuth flow
   - Verify success message

3. **User views missions**
   - `/missions`
   - Should see the "Test Mission"

4. **User posts mission**
   - `/post`
   - Select "Test Mission"
   - Select LinkedIn (or whichever platform you connected)
   - Verify post appears on your LinkedIn feed

5. **User checks score**
   - `/score`
   - Should show +10 points (or +15 if posted within 24h)

6. **Check leaderboard**
   - `/leaderboard`
   - Your name should appear with your score

7. **Sync role**
   - `/rolesync`
   - Should get "Recruit" role (0-49 points)

8. **Admin closes mission**
   - `/mission close 1` (use the mission ID from step 1)
   - Verify mission is closed

---

## ⚠️ Important Notes

### OAuth Setup
Make sure you've configured the OAuth redirect URLs correctly:
- **LinkedIn**: `https://afterprime-discordbot-Phantom200620.repl.co/oauth/linkedin/callback`
- **Meta**: `https://afterprime-discordbot-Phantom200620.repl.co/oauth/meta/callback`
- **TikTok**: `https://afterprime-discordbot-Phantom200620.repl.co/oauth/tiktok/callback`

### Instagram Requirements
- Users MUST have Instagram Business accounts (not personal)
- Business accounts must be linked to a Facebook Page
- Meta app must be in "Live" mode

### TikTok Requirements
- TikTok Content Posting API requires approval (may take days)
- Test with developer account first

### Bitly (Optional)
- Not configured yet (BITLY_ACCESS_TOKEN is empty)
- Click tracking will be disabled until configured

---

## 🐛 Troubleshooting

**Bot doesn't respond to commands:**
- Make sure bot has proper permissions in the server
- Check bot is online (should show as online in member list)
- Try restarting the bot workflow

**OAuth fails:**
- Verify redirect URLs match exactly in platform settings
- Check that secrets are set correctly
- Ensure platform apps are approved/live

**Role sync doesn't work:**
- Verify bot has "Manage Roles" permission
- Ensure bot's role is higher than the roles it's trying to assign
- Check that role IDs in secrets match your actual Discord roles

**Posts don't appear on social media:**
- Check console logs for API errors
- Verify platform tokens are valid
- Ensure you have proper permissions on the platform

---

## ✅ Testing Checklist

- [ ] Bot shows as online in Discord
- [ ] `/connect` shows platform selection
- [ ] OAuth flow completes successfully for at least one platform
- [ ] `/mission new` creates a new mission (admin only)
- [ ] Mission announcement appears in mission channel
- [ ] `/missions` displays active missions
- [ ] `/post` publishes to selected platform
- [ ] Post appears on actual social media platform
- [ ] `/score` shows updated points after posting
- [ ] `/leaderboard` displays rankings
- [ ] `/rolesync` assigns correct role
- [ ] `/mission close` closes a mission
- [ ] Closed missions don't appear in `/missions`

---

## 🎉 Success!

If all commands work as expected, your Social Army Discord Bot is fully functional and ready to use!

Next steps:
1. Invite your team members to test
2. Create real missions for your brand
3. Monitor engagement and leaderboard
4. Configure Bitly for click tracking (optional)
