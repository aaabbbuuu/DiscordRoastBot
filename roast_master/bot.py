import discord, asyncio, json, random
from discord.ext import commands
from .data_manager import DataManager
from .ai_engine import generate_roast

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
data_manager = DataManager("data/messages.json")

# Cooldown tracker to prevent spam
roast_cooldowns = {}

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print(f"📊 Loaded {len(data_manager.data)} users with message history")

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

def run_bot():
    with open("data/config.json") as f:
        config = json.load(f)
    bot.run(config["DISCORD_TOKEN"])