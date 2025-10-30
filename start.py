import asyncio
import threading
import uvicorn
from database import init_db

def run_oauth_server():
    from oauth_server import app
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

def run_discord_bot():
    from bot import bot
    import config
    bot.run(config.DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized!")
    
    print("Starting OAuth server on port 8000...")
    oauth_thread = threading.Thread(target=run_oauth_server, daemon=True)
    oauth_thread.start()
    
    print("Starting Discord bot...")
    run_discord_bot()
