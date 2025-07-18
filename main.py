import discord
from discord.ext import commands
from views import SuggestionButtons
from handlers import setup_handlers
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.add_view(SuggestionButtons())
    await setup_handlers(bot)
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Sync failed: {e}")

async def setup_extensions():
    await bot.load_extension("commands")

bot.loop.create_task(setup_extensions())
bot.run(os.getenv("DISCORD_TOKEN"))
