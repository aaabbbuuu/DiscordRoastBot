import discord, asyncio, json, random
from discord.ext import commands

# Try relative imports first (when in package), then absolute
try:
    from .data_manager import DataManager
    from .ai_engine import generate_roast
    from .history_fetcher import HistoryFetcher
except ImportError:
    from data_manager import DataManager
    from ai_engine import generate_roast
    from history_fetcher import HistoryFetcher

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
data_manager = DataManager("data/messages.json")
history_fetcher = HistoryFetcher(bot, data_manager)

# Cooldown tracker to prevent spam
roast_cooldowns = {}

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print(f"📊 Loaded {len(data_manager.data)} users with message history")
    print(f"📋 Commands registered: {', '.join([cmd.name for cmd in bot.commands])}")
    print(f"🏠 Connected to {len(bot.guilds)} server(s)")
    print("🔥 Bot is ready to roast!")

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors gracefully"""
    if isinstance(error, commands.CommandNotFound):
        # Silently ignore command not found errors
        pass
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need Administrator permissions to use this command!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument. Use `!help {ctx.command}` for usage info.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument. Make sure you're mentioning users with @username")
    else:
        print(f"❌ Error in command '{ctx.command}': {error}")
        await ctx.send(f"❌ An error occurred: {error}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Skip ALL command messages (anything starting with !)
    if not message.content.startswith("!"):
        # ✅ FIX: Store by user ID (not username) and only store non-command messages
        data_manager.add_message(message.author.id, message.content)
    
    await bot.process_commands(message)

@bot.command()
async def roast(ctx, member: discord.Member = None):
    """
    Roast a user based on their chat history.
    Usage: !roast @username or !roast (to roast yourself)
    """
    # If no member specified, roast the command author
    if member is None:
        member = ctx.author
    
    # Prevent self-roasting attempts on others
    if member.id == ctx.author.id and ctx.message.mentions:
        await ctx.send("🤔 Nice try, but you can't roast yourself by tagging yourself!")
        return
    
    # Cooldown check (30 seconds per user)
    user_key = f"{ctx.author.id}_{member.id}"
    if user_key in roast_cooldowns:
        time_left = 30 - (asyncio.get_event_loop().time() - roast_cooldowns[user_key])
        if time_left > 0:
            await ctx.send(f"⏳ Chill out! Wait {int(time_left)} seconds before roasting {member.display_name} again.")
            return
    
    # Show typing indicator for dramatic effect
    async with ctx.typing():
        user_data = data_manager.get_user_data(member.id)
        roast_text = await generate_roast(member.display_name, user_data)
        
        # Update cooldown
        roast_cooldowns[user_key] = asyncio.get_event_loop().time()
        
        await ctx.send(f"🔥 {member.mention} {roast_text}")

@bot.command()
async def stats(ctx, member: discord.Member = None):
    """
    Show message stats for a user.
    Usage: !stats @username or !stats (for yourself)
    """
    if member is None:
        member = ctx.author
    
    user_data = data_manager.get_user_data(member.id)
    msg_count = len(user_data.get("messages", []))
    
    if msg_count == 0:
        await ctx.send(f"👻 {member.display_name} is a ghost - no messages recorded!")
    else:
        avg_length = sum(len(m) for m in user_data["messages"]) / msg_count
        await ctx.send(
            f"📊 **Stats for {member.display_name}:**\n"
            f"💬 Messages recorded: {msg_count}\n"
            f"📏 Average message length: {avg_length:.1f} characters"
        )

@bot.command()
async def leaderboard(ctx):
    """Show the top 10 most active chatters"""
    if not data_manager.data:
        await ctx.send("📊 No message data yet!")
        return
    
    # Get all users with message counts
    user_counts = []
    for user_id, data in data_manager.data.items():
        msg_count = len(data.get("messages", []))
        if msg_count > 0:
            try:
                member = await ctx.guild.fetch_member(int(user_id))
                user_counts.append((member.display_name, msg_count))
            except:
                user_counts.append((f"Unknown User ({user_id})", msg_count))
    
    # Sort and get top 10
    user_counts.sort(key=lambda x: x[1], reverse=True)
    top_10 = user_counts[:10]
    
    leaderboard_text = "🏆 **Top Chatters:**\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, (name, count) in enumerate(top_10):
        medal = medals[i] if i < 3 else f"{i+1}."
        leaderboard_text += f"{medal} {name}: {count} messages\n"
    
    await ctx.send(leaderboard_text)

@bot.command()
async def roastme(ctx):
    """Roast yourself - for the brave souls"""
    async with ctx.typing():
        user_data = data_manager.get_user_data(ctx.author.id)
        roast_text = await generate_roast(ctx.author.display_name, user_data)
        await ctx.send(f"🔥 {ctx.author.mention} asked for it...\n{roast_text}")

@bot.command()
async def battle(ctx, member1: discord.Member, member2: discord.Member):
    """
    Roast battle between two users!
    Usage: !battle @user1 @user2
    """
    if member1.bot or member2.bot:
        await ctx.send("🤖 Bots are immune to roasts!")
        return
    
    async with ctx.typing():
        user_data1 = data_manager.get_user_data(member1.id)
        user_data2 = data_manager.get_user_data(member2.id)
        
        roast1 = await generate_roast(member1.display_name, user_data1)
        await asyncio.sleep(1)  # Dramatic pause
        roast2 = await generate_roast(member2.display_name, user_data2)
        
        await ctx.send(
            f"⚔️ **ROAST BATTLE!** ⚔️\n\n"
            f"🔥 {member1.mention}:\n{roast1}\n\n"
            f"💥 {member2.mention}:\n{roast2}\n\n"
            f"Vote with reactions! 1️⃣ for {member1.display_name}, 2️⃣ for {member2.display_name}"
        )
        
        # Add reaction options
        message = await ctx.channel.fetch_message(ctx.channel.last_message_id)
        await message.add_reaction("1️⃣")
        await message.add_reaction("2️⃣")

@bot.command()
@commands.has_permissions(administrator=True)
async def index(ctx, days: int = 30):
    """
    [ADMIN ONLY] Index chat history from this channel
    Usage: !index [days] - defaults to 30 days
    """
    if days > 365:
        await ctx.send("⚠️ Maximum 365 days allowed!")
        return
    
    status_msg = await ctx.send(f"📚 Starting to index last {days} days of chat history in #{ctx.channel.name}...")
    
    result = await history_fetcher.index_channel_history(ctx.channel, days)
    
    if result["success"]:
        top_users = "\n".join([f"  • {name}: {count} messages" for name, count in result["top_users"]])
        await status_msg.edit(content=
            f"✅ **Indexing Complete!**\n"
            f"📊 Indexed {result['message_count']} messages from {result['user_count']} users\n\n"
            f"🏆 **Top Contributors:**\n{top_users}"
        )
    else:
        await status_msg.edit(content=f"❌ Failed to index: {result.get('error', 'Unknown error')}")

@bot.command()
@commands.has_permissions(administrator=True)
async def indexserver(ctx, days: int = 30):
    """
    [ADMIN ONLY] Index entire server's chat history
    Usage: !indexserver [days] - defaults to 30 days
    WARNING: This may take a while!
    """
    if days > 365:
        await ctx.send("⚠️ Maximum 365 days allowed!")
        return
    
    status_msg = await ctx.send(f"🏰 Starting server-wide index for last {days} days...\nThis may take several minutes!")
    
    async def progress_update(message):
        try:
            await status_msg.edit(content=f"📚 {message}")
        except:
            pass
    
    result = await history_fetcher.index_server_history(ctx.guild, days, progress_update)
    
    failed_text = ""
    if result["failed_channels"]:
        failed_text = f"\n⚠️ Couldn't access: {', '.join(result['failed_channels'][:5])}"
    
    await status_msg.edit(content=
        f"✅ **Server Index Complete!**\n"
        f"📊 Indexed {result['total_messages']} messages\n"
        f"📝 From {result['successful_channels']}/{result['total_channels']} channels"
        f"{failed_text}"
    )

@bot.command()
@commands.has_permissions(administrator=True)
async def deepdive(ctx, member: discord.Member, days: int = 90):
    """
    [ADMIN ONLY] Deep dive into a user's history across all channels
    Usage: !deepdive @user [days] - defaults to 90 days
    """
    if days > 365:
        await ctx.send("⚠️ Maximum 365 days allowed!")
        return
    
    status_msg = await ctx.send(f"🔍 Deep-diving into {member.display_name}'s history...")
    
    count = await history_fetcher.fetch_user_deep_history(ctx.guild, member, days)
    
    await status_msg.edit(content=
        f"✅ **Deep Dive Complete!**\n"
        f"Found {count} messages from {member.display_name} across all channels"
    )

@bot.command()
async def embarrass(ctx, member: discord.Member):
    """
    Find and roast someone based on their most embarrassing messages
    Usage: !embarrass @user
    """
    if member.bot:
        await ctx.send("🤖 Bots don't get embarrassed!")
        return
    
    async with ctx.typing():
        # Find embarrassing moments
        embarrassing = await history_fetcher.find_embarrassing_moments(member.id)
        
        if not embarrassing:
            await ctx.send(f"🤔 Couldn't find anything embarrassing from {member.mention}... yet.")
            return
        
        # Create a special roast using embarrassing context
        user_data = data_manager.get_user_data(member.id)
        
        # Add embarrassing messages to the roast context
        user_data["embarrassing_context"] = embarrassing[:3]  # Top 3 most embarrassing
        
        roast_text = await generate_roast(member.display_name, user_data)
        
        await ctx.send(f"😬 {member.mention}\n{roast_text}")

@bot.command()
async def memory(ctx, member: discord.Member = None):
    """
    Show how much chat history the bot has stored
    Usage: !memory [@user] - shows your own or another user's stored message count
    """
    if member is None:
        member = ctx.author
    
    user_data = data_manager.get_user_data(member.id)
    msg_count = len(user_data.get("messages", []))
    total_count = user_data.get("total_messages", msg_count)
    
    first_seen = user_data.get("first_seen", "Unknown")
    if first_seen != "Unknown":
        from datetime import datetime
        first_date = datetime.fromisoformat(first_seen).strftime("%Y-%m-%d")
        first_seen = first_date
    
    await ctx.send(
        f"🧠 **Memory Stats for {member.display_name}:**\n"
        f"💾 Currently stored: {msg_count} messages\n"
        f"📊 Total seen: {total_count} messages\n"
        f"📅 First seen: {first_seen}"
    )

def run_bot():
    with open("data/config.json") as f:
        config = json.load(f)
    bot.run(config["DISCORD_TOKEN"])