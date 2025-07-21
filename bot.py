import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

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
        token = os.getenv("BOT_TOKEN")
        if not token:
            raise RuntimeError("⚠️ BOT_TOKEN not set in environment")
        await bot.start(token)

asyncio.run(main())