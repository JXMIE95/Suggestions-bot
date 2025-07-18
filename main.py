import discord
from discord.ext import commands
import asyncio
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()

async def load_extensions():
    await bot.load_extension("commands")

asyncio.run(load_extensions())

bot.run(os.getenv("DISCORD_TOKEN"))
