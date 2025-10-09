#!/usr/bin/env python3
"""
DankRoastMaster 3000 - Discord Roast Bot
Entry point for the application
"""

import os
import sys

# Ensure data directory exists
if not os.path.exists("data"):
    os.makedirs("data")
    print("📁 Created data directory")

# Check for config file
if not os.path.exists("data/config.json"):
    print("❌ ERROR: data/config.json not found!")
    print("Please create data/config.json with your API keys:")
    print("""
{
  "DISCORD_TOKEN": "your_discord_bot_token",
  "OPENAI_API_KEY": "your_openai_key",
  "GROQ_API_KEY": "your_groq_key"
}
    """)
    sys.exit(1)

# Import and run bot
try:
    # Try importing from roast_master package
    from roast_master.bot import run_bot
    print("🔥 Starting DankRoastMaster 3000...")
    run_bot()
except ImportError:
    try:
        # Fallback: try importing from current directory
        from bot import run_bot
        print("🔥 Starting DankRoastMaster 3000...")
        run_bot()
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure all required files are present:")
        print("  - roast_master/bot.py")
        print("  - roast_master/ai_engine.py")
        print("  - roast_master/data_manager.py")
        print("  - roast_master/history_fetcher.py")
        sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)