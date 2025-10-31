import asyncio
import threading
import uvicorn
from database import init_db

def run_oauth_server():
    from oauth_server import app
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

async def run_discord_bot_async():
    from bot import bot
    from engagement_workers import engagement_worker
    import config
    
    print("Starting engagement tracking workers...")
    await engagement_worker.start()
    
    print("Starting Discord bot...")
    await bot.start(config.DISCORD_BOT_TOKEN)

def run_discord_bot():
    try:
        asyncio.run(run_discord_bot_async())
    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == "__main__":
    print("=" * 60)
    print("Social Army Discord Bot - Multi-Platform Edition")
    print("Supported: LinkedIn, Instagram/Meta, TikTok")
    print("=" * 60)
    
    print("\nInitializing database...")
    init_db()
    print("✓ Database initialized!")
    
    print("\nStarting OAuth server on port 8000...")
    oauth_thread = threading.Thread(target=run_oauth_server, daemon=True)
    oauth_thread.start()
    print("✓ OAuth server running!")
    
    print("\nStarting Discord bot and engagement workers...")
    run_discord_bot()
