#!/usr/bin/env python3
"""
Diagnostic script to test if commands are registering properly
Run this to verify your bot setup
"""

import discord
from discord.ext import commands
import json

# Setup
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user}")
    print(f"📋 Registered commands: {[cmd.name for cmd in bot.commands]}")
    print(f"🏠 Connected to {len(bot.guilds)} server(s)")
    
@bot.command()
async def ping(ctx):
    """Test command to verify bot is working"""
    await ctx.send("🏓 Pong! Bot is working!")

@bot.command()
async def test(ctx):
    """Another test command"""
    await ctx.send("✅ Test command works!")

@bot.command()
@commands.has_permissions(administrator=True)
async def admintest(ctx):
    """Test admin command"""
    await ctx.send("✅ Admin command works! You have administrator permissions.")

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"❌ Command not found. Try `!ping` or `!help`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(f"❌ You don't have permission to use this command")
    else:
        print(f"Error: {error}")
        await ctx.send(f"❌ Error: {error}")

# Run
if __name__ == "__main__":
    with open("data/config.json") as f:
        config = json.load(f)
    
    print("🔥 Starting diagnostic bot...")
    print("Commands to test:")
    print("  !ping - Basic test")
    print("  !test - Another test")
    print("  !admintest - Admin test (requires admin permissions)")
    print("  !help - Show all commands")
    print()
    
    bot.run(config["DISCORD_TOKEN"])