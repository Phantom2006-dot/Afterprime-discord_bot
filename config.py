import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_GUILD_ID = int(os.getenv('DISCORD_GUILD_ID', 0))
ADMIN_ROLE_NAME = os.getenv('ADMIN_ROLE_NAME', 'Admin')

BASE_URL = os.getenv('BASE_URL', 'http://localhost:8000')

LINKEDIN_CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID')
LINKEDIN_CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET')
LINKEDIN_REDIRECT_URI = f"{BASE_URL}/oauth/linkedin/callback"

META_APP_ID = os.getenv('META_APP_ID')
META_APP_SECRET = os.getenv('META_APP_SECRET')
META_REDIRECT_URI = f"{BASE_URL}/oauth/meta/callback"

TIKTOK_CLIENT_KEY = os.getenv('TIKTOK_CLIENT_KEY')
TIKTOK_CLIENT_SECRET = os.getenv('TIKTOK_CLIENT_SECRET')
TIKTOK_REDIRECT_URI = f"{BASE_URL}/oauth/tiktok/callback"

BITLY_ACCESS_TOKEN = os.getenv('BITLY_ACCESS_TOKEN')

DATABASE_URL = os.getenv('DATABASE_URL')

ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

RECRUIT_ROLE_ID = int(os.getenv('RECRUIT_ROLE_ID', 0))
SOLDIER_ROLE_ID = int(os.getenv('SOLDIER_ROLE_ID', 0))
GENERAL_ROLE_ID = int(os.getenv('GENERAL_ROLE_ID', 0))
WARLORD_ROLE_ID = int(os.getenv('WARLORD_ROLE_ID', 0))

MISSION_CHANNEL_ID = int(os.getenv('MISSION_CHANNEL_ID', 0))
AUDIT_CHANNEL_ID = int(os.getenv('AUDIT_CHANNEL_ID', 0))

ROLE_THRESHOLDS = {
    'Recruit': 0,
    'Soldier': 50,
    'General': 200,
    'Warlord': 500
}

SCORING = {
    'publish_success': 10,
    'on_time_bonus': 5,
    'clicks_per_10': 1,
    'linkedin_reactions_10': 5,
    'linkedin_reactions_30': 10,
    'linkedin_reactions_100': 20,
    'instagram_views_100': 5,
    'instagram_views_500': 10,
    'instagram_views_2000': 20,
    'tiktok_views_100': 5,
    'tiktok_views_500': 10,
    'tiktok_views_2000': 20,
    'top_clicker_1': 25,
    'top_clicker_2': 15,
    'top_clicker_3': 10
}

PLATFORM_SCOPES = {
    'linkedin': ['w_member_social', 'r_liteprofile', 'r_basicprofile'],
    'meta': ['pages_manage_posts', 'pages_read_engagement', 'pages_show_list', 'instagram_basic', 'instagram_content_publish'],
    'tiktok': ['video.upload', 'user.info.basic']
}

METRICS_POLL_INTERVAL = int(os.getenv('METRICS_POLL_INTERVAL', 3600))
CLICKS_POLL_INTERVAL = int(os.getenv('CLICKS_POLL_INTERVAL', 300))
