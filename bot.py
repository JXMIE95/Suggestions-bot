import discord
from discord.ext import commands
import asyncio
import json
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

async def main():
    async with bot:
        await bot.load_extension("cogs.suggestions")
        await bot.load_extension("cogs.scheduler")
        await bot.start(os.getenv("BOT_TOKEN") or json.load(open("config.json"))["token"])

asyncio.run(main())
