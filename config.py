import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_GUILD_ID = int(os.getenv('DISCORD_GUILD_ID', 0))
ADMIN_ROLE_NAME = os.getenv('ADMIN_ROLE_NAME', 'Admin')

DATABASE_URL = os.getenv('DATABASE_URL')

SOCIAL_ARMY_CHANNEL_ID = int(os.getenv('SOCIAL_ARMY_CHANNEL_ID', 0))
SOCIAL_ARMY_JUDGE_ROLE_NAME = os.getenv('SOCIAL_ARMY_JUDGE_ROLE_NAME', 'Social Army Judge')
SOCIAL_ARMY_ELITE_ROLE_NAME = os.getenv('SOCIAL_ARMY_ELITE_ROLE_NAME', 'Social Army Elite')
LEADERBOARD_SIZE = int(os.getenv('LEADERBOARD_SIZE', 10))

EMOJI_POINTS = {
    '✍️': 1,
    '🎨': 3,
    '🎬': 5,
    '🎞️': 8,
    '💡': 2,
    '🤯': 4,
    '📊': 2,
    '🔥': 4,
    '🚀': 8,
    '🧡': 2,
    '💪': 3,
    '🏅': 5,
    '👑': 10
}

OWNER_ONLY_EMOJIS = ['🏅', '👑']
