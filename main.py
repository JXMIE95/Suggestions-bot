import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

channels = {
    "suggestions": None,
    "main": None,
    "staff": None,
    "announcement": None
}

roles = {
    "diplomat": None,
    "main": None,
    "announcement": None
}

active_polls = {}

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.tree.sync()
    check_poll_timeouts.start()

@bot.tree.command(name="setup", description="Set up suggestion system channels and roles.")
@app_commands.describe(
    suggestions_channel="Channel where users submit suggestions.",
    main_channel="Channel where suggestions are posted for voting.",
    staff_channel="Channel where staff polls are held.",
    announcement_channel="Channel for final announcements.",
    diplomat_role="Role that votes on suggestions.",
    main_role="Role to mention in main channel.",
    announcement_role="Role to mention in announcements."
)
async def setup(
    interaction: discord.Interaction,
    suggestions_channel: discord.TextChannel,
    main_channel: discord.TextChannel,
    staff_channel: discord.TextChannel,
    announcement_channel: discord.TextChannel,
    diplomat_role: discord.Role = None,
    main_role: discord.Role = None,
    announcement_role: discord.Role = None
):
    channels["suggestions"] = suggestions_channel.id
    channels["main"] = main_channel.id
    channels["staff"] = staff_channel.id
    channels["announcement"] = announcement_channel.id

    roles["diplomat"] = diplomat_role.id if diplomat_role else None
    roles["main"] = main_role.id if main_role else None
    roles["announcement"] = announcement_role.id if announcement_role else None

    await interaction.response.send_message("✅ Setup complete.", ephemeral=True)

@bot.tree.command(name="suggest", description="Submit a suggestion.")
@app_commands.describe(title="Title of the suggestion", description="Describe your suggestion")
async def suggest(interaction: discord.Interaction, title: str, description: str):
    if channels["main"] is None:
        await interaction.response.send_message("❌ Suggestion system is not fully set up.", ephemeral=True)
        return

    embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
    embed.set_footer(text=f"Suggested by {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)

    main_channel = bot.get_channel(channels["main"])
    mention = f"<@&{roles['main']}>" if roles["main"] else ""
    message = await main_channel.send(content=mention, embed=embed)
    await message.add_reaction("👍")
    await message.add_reaction("👎")

    await interaction.response.send_message("✅ Your suggestion has been submitted!", ephemeral=True)

    active_polls[message.id] = {
        "message": message,
        "original_embed": embed,
        "author_id": interaction.user.id,
        "start_time": datetime.utcnow(),
        "voters": set()
    }

@tasks.loop(seconds=60)
async def check_poll_timeouts():
    now = datetime.utcnow()
    to_remove = []

    for msg_id, poll in list(active_polls.items()):
        if now - poll["start_time"] > timedelta(hours=24):
            staff_channel = bot.get_channel(channels["staff"])
            diplomat_role = f"<@&{roles['diplomat']}>" if roles["diplomat"] else ""

            poll_embed = discord.Embed(
                title="Diplomat Poll",
                description=f"{poll['original_embed'].description}",
                color=discord.Color.gold()
            )
            poll_embed.set_footer(text=poll['original_embed'].footer.text)

            poll_message = await staff_channel.send(content=diplomat_role, embed=poll_embed)
            await poll_message.add_reaction("✅")
            await poll_message.add_reaction("❌")

            poll["poll_message_id"] = poll_message.id
            poll["poll_channel_id"] = staff_channel.id
            poll["poll_start_time"] = now
            poll["voted_users"] = set()

            to_remove.append(msg_id)

    for msg_id in to_remove:
        del active_polls[msg_id]

bot.run(TOKEN)