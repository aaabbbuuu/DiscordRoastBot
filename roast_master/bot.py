import discord, asyncio, json
from discord.ext import commands
from .data_manager import DataManager
from .ai_engine import generate_roast

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
data_manager = DataManager("data/messages.json")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.name == "general":
        data_manager.add_message(message.author.id, message.content)
    await bot.process_commands(message)

@bot.command()
async def roast(ctx, member: discord.Member):
    user_data = data_manager.get_user_data(member.id)
    roast_text = await generate_roast(member.display_name, user_data)
    await ctx.send(f"🔥 {roast_text}")

def run_bot():
    with open("data/config.json") as f:
        config = json.load(f)
    bot.run(config["DISCORD_TOKEN"])
