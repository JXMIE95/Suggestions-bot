import discord
from discord.ext import commands
from discord import app_commands
import json
import os

TOKEN = os.getenv("DISCORD_TOKEN")
SETTINGS_FILE = "settings.json"

class SuggestionBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.settings = self.load_settings()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        else:
            return {
                "channels": {
                    "suggestions": None,
                    "main": None,
                    "staff": None,
                    "announcement": None
                },
                "roles": {
                    "staff": None,
                    "announce": None
                }
            }

    def save_settings(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=4)

bot = SuggestionBot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    await bot.tree.sync()

@bot.tree.command(name="set_channel", description="Set a channel for a specific purpose.")
@app_commands.describe(type="Type of channel", channel="Channel to use")
@app_commands.choices(type=[
    app_commands.Choice(name="suggestions", value="suggestions"),
    app_commands.Choice(name="main", value="main"),
    app_commands.Choice(name="staff", value="staff"),
    app_commands.Choice(name="announcement", value="announcement")
])
async def set_channel(interaction: discord.Interaction, type: app_commands.Choice[str], channel: discord.TextChannel):
    bot.settings["channels"][type.value] = channel.id
    bot.save_settings()
    await interaction.response.send_message(f"✅ Set **{type.value}** channel to {channel.mention}", ephemeral=True)

@bot.tree.command(name="set_role", description="Set a role for a specific purpose.")
@app_commands.describe(type="Type of role", role="Role to use")
@app_commands.choices(type=[
    app_commands.Choice(name="staff", value="staff"),
    app_commands.Choice(name="announce", value="announce")
])
async def set_role(interaction: discord.Interaction, type: app_commands.Choice[str], role: discord.Role):
    bot.settings["roles"][type.value] = role.id
    bot.save_settings()
    await interaction.response.send_message(f"✅ Set **{type.value}** role to {role.mention}", ephemeral=True)

@bot.tree.command(name="view_settings", description="View current channel and role settings.")
async def view_settings(interaction: discord.Interaction):
    embed = discord.Embed(title="Current Bot Settings", color=discord.Color.blue())
    for key, val in bot.settings["channels"].items():
        mention = f"<#{val}>" if val else "❌ Not set"
        embed.add_field(name=f"{key.capitalize()} Channel", value=mention, inline=False)
    for key, val in bot.settings["roles"].items():
        mention = f"<@&{val}>" if val else "❌ Not set"
        embed.add_field(name=f"{key.capitalize()} Role", value=mention, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

bot.run(TOKEN)