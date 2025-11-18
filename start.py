import asyncio
from database import init_db

async def run_discord_bot_async():
    from bot import bot
    import config
    
    print("Starting Discord bot...")
    await bot.start(config.DISCORD_BOT_TOKEN)

def run_discord_bot():
    try:
        asyncio.run(run_discord_bot_async())
    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == "__main__":
    print("=" * 60)
    print("Social Army Discord Bot - Reaction-Based Scoring")
    print("=" * 60)
    
    print("\nInitializing database...")
    init_db()
    print("✓ Database initialized!")
    
    print("\nStarting Discord bot...")
    run_discord_bot()
