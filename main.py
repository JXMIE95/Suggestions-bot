mport discord
from discord.ext import commands, tasks
from discord import app_commands
import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timedelta

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

config = {
    "suggestion_channel": None,
    "main_channel": None,
    "staff_channel": None,
    "announcement_channel": None,
    "staff_role": None,
    "announcement_role": None,
    "main_role": None,
}

polls = {}

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@tree.command(name="setup", description="Set up the suggestion system")
@app_commands.describe(
    suggestion_channel="Channel for suggestions",
    main_channel="Channel for main announcements",
    staff_channel="Channel for staff polls",
    announcement_channel="Channel for final announcements",
    staff_role="Role for staff (Diplomats)",
    main_role="Role to mention in main channel",
    announcement_role="Role to mention in announcement channel"
)
async def setup(
    interaction: discord.Interaction,
    suggestion_channel: discord.TextChannel,
    main_channel: discord.TextChannel,
    staff_channel: discord.TextChannel,
    announcement_channel: discord.TextChannel,
    staff_role: discord.Role = None,
    main_role: discord.Role = None,
    announcement_role: discord.Role = None
):
    config["suggestion_channel"] = suggestion_channel.id
    config["main_channel"] = main_channel.id
    config["staff_channel"] = staff_channel.id
    config["announcement_channel"] = announcement_channel.id
    config["staff_role"] = staff_role.id if staff_role else None
    config["main_role"] = main_role.id if main_role else None
    config["announcement_role"] = announcement_role.id if announcement_role else None

    await interaction.response.send_message("✅ Setup complete!", ephemeral=True)

@tree.command(name="suggest", description="Make a suggestion")
@app_commands.describe(title="Title of the suggestion", description="Describe your suggestion")
async def suggest(interaction: discord.Interaction, title: str, description: str):
    channel = bot.get_channel(config["suggestion_channel"])
    embed = discord.Embed(title=title, description=description, color=discord.Color.blurple())
    embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.timestamp = datetime.utcnow()
    message = await channel.send(embed=embed)
    await message.add_reaction("👍")
    await message.add_reaction("👎")
    await interaction.response.send_message("✅ Suggestion sent!", ephemeral=True)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.channel_id != config["staff_channel"]:
        return

    if payload.message_id in polls:
        poll = polls[payload.message_id]
        guild = bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)

        if not member or member.bot:
            return

        if payload.emoji.name == "✅":
            poll["yes"] += 1
            poll["votes"].add(payload.user_id)
        elif payload.emoji.name == "❌":
            poll["no"] += 1
            poll["votes"].add(payload.user_id)

        diplomat_role = guild.get_role(config["staff_role"])
        diplomat_members = [m.id for m in diplomat_role.members if not m.bot]

        if set(diplomat_members).issubset(poll["votes"]):
            await send_poll_result(payload.message_id, guild)
            del polls[payload.message_id]

async def send_poll_result(poll_id, guild):
    poll = polls[poll_id]
    announcement_channel = guild.get_channel(config["announcement_channel"])
    announcement_role = f"<@&{config['announcement_role']}>" if config["announcement_role"] else ""

    passed = poll["yes"] > poll["no"]
    result_text = (
        "✅ The following suggestion has been passed by the Diplomats"
        if passed else
        "❌ Suggestion Rejected by Diplomats"
    )

    color = 0x2ecc71 if passed else 0xe74c3c

    embed = discord.Embed(
        title="📢 Poll Result",
        description=f"{poll['original_embed'].description}

**{result_text}**",
        color=color
    )
    await announcement_channel.send(content=announcement_role, embed=embed)

async def start_staff_poll(message):
    polls[message.id] = {
        "yes": 0,
        "no": 0,
        "votes": set(),
        "original_embed": message.embeds[0],
        "start_time": datetime.utcnow()
    }
    await message.add_reaction("✅")
    await message.add_reaction("❌")
    await message.channel.send("🗳️ Diplomat Poll started. Vote now!")

@tasks.loop(minutes=1)
async def check_poll_timeouts():
    now = datetime.utcnow()
    expired_polls = [mid for mid, poll in polls.items() if now - poll["start_time"] >= timedelta(hours=24)]
    for mid in expired_polls:
        guild = bot.guilds[0]
        await send_poll_result(mid, guild)
        del polls[mid]

@bot.event
async def on_message(message):
    if message.channel.id == config["suggestion_channel"] and message.author != bot.user:
        staff_channel = bot.get_channel(config["staff_channel"])
        staff_role = f"<@&{config['staff_role']}>" if config["staff_role"] else ""
        embed = discord.Embed(title="New Suggestion", description=message.content, color=discord.Color.orange())
        embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url if message.author.avatar else None)
        poll_msg = await staff_channel.send(content=staff_role, embed=embed)
        await start_staff_poll(poll_msg)
    await bot.process_commands(message)

check_poll_timeouts.start()
bot.run(TOKEN)