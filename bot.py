import os
from discord.ext import commands
from discord import Intents, Activity, ActivityType
from dotenv import load_dotenv

load_dotenv()

intents = Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

async def load_cogs():
    cogs = ["profile", "upload"]
    for cog in cogs:
        try:
            await bot.load_extension(f"cogs.{cog}")
            print(f"✅ Cog loaded successfully: {cog}")
        except Exception as e:
            print(f"❌ Failed to load cog {cog}: {str(e)}")

@bot.event
async def on_ready():
    activity = Activity(name="Prototype 2", type=ActivityType.playing)
    await bot.change_presence(activity=activity)
    print(f'Logged in as {bot.user}')
    print(f'Bot is in {len(bot.guilds)} guilds')

    await load_cogs()

    # Logging command tree
    print("Current command tree:")
    for command in bot.tree.get_commands():
        print(f"- {command.name}, Description: {command.description}")

    print("Syncing slash commands...")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Failed to sync slash commands: {str(e)}")
        # Additional logging to investigate the issue
        for command in bot.tree.get_commands():
            print(f"Command: {command.name}, Description: {command.description}")

token = os.getenv('tkn')
bot.run(token)