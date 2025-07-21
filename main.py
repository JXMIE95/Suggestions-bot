import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timedelta

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@tasks.loop(hours=24)
async def trigger_week_schedule():
    now = datetime.utcnow()
    if now.weekday() == 0 and now.hour == 0:  # Every Monday 00:00 UTC
        cog = bot.get_cog("BuffScheduler")
        if cog:
            for guild in bot.guilds:
                await cog.run_generate_schedule(guild)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    trigger_week_schedule.start()

async def load_extensions():
    await bot.load_extension("bot.scheduler")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

asyncio.run(main())
