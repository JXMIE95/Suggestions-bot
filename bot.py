import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔁 Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Command sync failed:", e)

async def main():
    async with bot:
        await bot.load_extension("cogs.suggestions")
        await bot.load_extension("cogs.scheduler")
        await bot.load_extension("cogs.config_commands")
        await bot.start(os.getenv("BOT_TOKEN"))

asyncio.run(main())
