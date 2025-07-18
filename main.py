import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
from suggestion import SuggestionView

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

class SuggestionBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

bot = SuggestionBot()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

@bot.tree.command(name="setup_buttons", description="Set up suggestion buttons in this channel.")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def setup_buttons(interaction: discord.Interaction):
    await interaction.response.send_message("✅ Buttons added!", view=SuggestionView(), ephemeral=False)

bot.run(TOKEN)
