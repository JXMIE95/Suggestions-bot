import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

class SuggestionBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.config = {
            "suggestion_channel_id": None,
            "main_channel_id": None,
            "staff_channel_id": None,
            "announcement_channel_id": None,
            "staff_role_id": None,
            "announcement_role_id": None
        }

    async def setup_hook(self):
        self.tree.copy_global_to(guild=None)
        await self.tree.sync()

bot = SuggestionBot()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

@bot.tree.command(name="set_channel", description="Set a channel for suggestions or announcements.")
@app_commands.describe(type="The type of channel to set (suggestion, main, staff, announcement)")
async def set_channel(interaction: discord.Interaction, type: str, channel: discord.TextChannel):
    bot.config[f"{type}_channel_id"] = channel.id
    await interaction.response.send_message(f"{type.capitalize()} channel set to {channel.mention}", ephemeral=True)

@bot.tree.command(name="set_role", description="Set a role for staff or announcement mentions.")
@app_commands.describe(type="The type of role to set (staff, announcement)")
async def set_role(interaction: discord.Interaction, type: str, role: discord.Role):
    bot.config[f"{type}_role_id"] = role.id
    await interaction.response.send_message(f"{type.capitalize()} role set to {role.mention}", ephemeral=True)

@bot.tree.command(name="setup_buttons", description="Post the suggestion buttons in the current channel.")
async def setup_buttons(interaction: discord.Interaction):
    view = SuggestionButtons()
    await interaction.response.send_message("Choose an option:", view=view)

class SuggestionButtons(discord.ui.View):
    @discord.ui.button(label="Make a Suggestion", style=discord.ButtonStyle.green)
    async def make_suggestion(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = SuggestionModal()
        await interaction.response.send_modal(modal)

class SuggestionModal(discord.ui.Modal, title="Submit a Suggestion"):
    suggestion_title = discord.ui.TextInput(label="Title", max_length=100)
    suggestion_desc = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, max_length=1000)

    async def on_submit(self, interaction: discord.Interaction):
        main_channel = bot.get_channel(bot.config["main_channel_id"])
        embed = discord.Embed(title=self.suggestion_title.value, description=self.suggestion_desc.value, color=discord.Color.blue())
        embed.set_footer(text=f"Suggested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        msg = await main_channel.send("@everyone", embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        await interaction.response.send_message("✅ Suggestion submitted!", ephemeral=True)
        check_likes.start(msg)

@tasks.loop(seconds=30.0, count=48)  # 24 hours max
async def check_likes(message: discord.Message):
    await message.fetch()
    thumbs_up = discord.utils.get(message.reactions, emoji="👍")
    if thumbs_up and thumbs_up.count - 1 >= 10:
        staff_channel = bot.get_channel(bot.config["staff_channel_id"])
        staff_role = message.guild.get_role(bot.config["staff_role_id"])
        poll_msg = await staff_channel.send(f"{staff_role.mention} Please vote on this suggestion:", embed=message.embeds[0])
        await poll_msg.add_reaction("✅")
        await poll_msg.add_reaction("❌")
        check_votes.start(poll_msg, message.embeds[0])
        check_likes.stop()

@tasks.loop(seconds=60.0, count=24*60)
async def check_votes(poll_msg: discord.Message, original_embed: discord.Embed):
    await poll_msg.fetch()
    yes_votes = discord.utils.get(poll_msg.reactions, emoji="✅")
    no_votes = discord.utils.get(poll_msg.reactions, emoji="❌")
    staff_role = poll_msg.guild.get_role(bot.config["staff_role_id"])
    total_staff = len([m for m in poll_msg.guild.members if staff_role in m.roles])
    total_votes = (yes_votes.count if yes_votes else 0) + (no_votes.count if no_votes else 0) - 2
    if total_votes >= total_staff:
        announcement_channel = bot.get_channel(bot.config["announcement_channel_id"])
        announce_role = poll_msg.guild.get_role(bot.config["announcement_role_id"])
        result = "✅ Approved!" if (yes_votes.count - 1) > (no_votes.count - 1) else "❌ Rejected!"
        await announcement_channel.send(f"{announce_role.mention} {result}", embed=original_embed)
        check_votes.stop()

bot.run(TOKEN)
