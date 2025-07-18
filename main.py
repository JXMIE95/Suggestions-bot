import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", 0))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID)) if GUILD_ID else await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="setup", description="Set up the bot", guild=discord.Object(id=GUILD_ID) if GUILD_ID else None)
async def setup_command(interaction: discord.Interaction):
    await interaction.response.send_message("Setup complete! ✅", ephemeral=True)

bot.run(TOKEN)
