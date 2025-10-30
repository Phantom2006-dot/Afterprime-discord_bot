import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_GUILD_ID = int(os.getenv('DISCORD_GUILD_ID', 0))
ADMIN_ROLE_NAME = os.getenv('ADMIN_ROLE_NAME', 'Admin')

LINKEDIN_CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID')
LINKEDIN_CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET')
OAUTH_REDIRECT_URI = os.getenv('OAUTH_REDIRECT_URI', 'http://localhost:8000/oauth/linkedin/callback')

DATABASE_URL = os.getenv('DATABASE_URL')

ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

RECRUIT_ROLE_ID = int(os.getenv('RECRUIT_ROLE_ID', 0))
SOLDIER_ROLE_ID = int(os.getenv('SOLDIER_ROLE_ID', 0))
GENERAL_ROLE_ID = int(os.getenv('GENERAL_ROLE_ID', 0))
WARLORD_ROLE_ID = int(os.getenv('WARLORD_ROLE_ID', 0))

MISSION_CHANNEL_ID = int(os.getenv('MISSION_CHANNEL_ID', 0))

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
    'linkedin_reactions_100': 20
}
