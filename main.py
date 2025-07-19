import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import os

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.reactions = True

TOKEN = os.getenv("DISCORD_TOKEN")

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Channel and role IDs
config = {
    "suggestion_channel": None,
    "main_channel": None,
    "staff_channel": None,
    "announcement_channel": None,
    "main_role": None,
    "staff_role": None,
    "announcement_role": None,
}

LIKE_THRESHOLD = 10
polls = {}  # message_id -> {"voters": set, "yes": int, "no": int}

@tree.command(name="setup", description="Configure all suggestion bot channels and roles")
@app_commands.describe(
    suggestion_channel="Channel where suggestions are submitted",
    main_channel="Channel where suggestions are posted",
    staff_channel="Channel where staff vote on suggestions",
    announcement_channel="Channel where final announcements are made",
    main_role="Role to mention in main channel (optional)",
    staff_role="Role to mention in staff channel (optional)",
    announcement_role="Role to mention in announcement channel (optional)"
)
async def setup(
    interaction: discord.Interaction,
    suggestion_channel: discord.TextChannel,
    main_channel: discord.TextChannel,
    staff_channel: discord.TextChannel,
    announcement_channel: discord.TextChannel,
    main_role: discord.Role = None,
    staff_role: discord.Role = None,
    announcement_role: discord.Role = None,
):
    config.update({
        "suggestion_channel": suggestion_channel.id,
        "main_channel": main_channel.id,
        "staff_channel": staff_channel.id,
        "announcement_channel": announcement_channel.id,
        "main_role": main_role.id if main_role else None,
        "staff_role": staff_role.id if staff_role else None,
        "announcement_role": announcement_role.id if announcement_role else None,
    })
    await interaction.response.send_message("✅ Channels and roles configured!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print("❌ Failed to sync commands:", e)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if config["suggestion_channel"] and message.channel.id == config["suggestion_channel"]:
        main_channel = bot.get_channel(config["main_channel"])
        main_role_id = config["main_role"]
        mention = f"<@&{main_role_id}>" if main_role_id else ""

        embed = discord.Embed(
            title="New Suggestion",
            description=message.content,
            color=discord.Color.blue()
        )
        sent = await main_channel.send(content=mention, embed=embed)
        await sent.add_reaction("👍")
        await sent.add_reaction("👎")

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    message = reaction.message
    if message.author != bot.user:
        return

    if str(reaction.emoji) != "👍":
        return

    if config["main_channel"] and message.channel.id != config["main_channel"]:
        return

    thumbs_up = discord.utils.get(message.reactions, emoji="👍")
    if thumbs_up and thumbs_up.count >= LIKE_THRESHOLD:
        # Already handled
        if message.id in polls:
            return

        staff_channel = bot.get_channel(config["staff_channel"])
        staff_role_id = config["staff_role"]
        mention = f"<@&{staff_role_id}>" if staff_role_id else ""

        embed = discord.Embed(
            title="Staff Review Required",
            description=message.embeds[0].description,
            color=discord.Color.orange()
        )
        poll_msg = await staff_channel.send(content=mention, embed=embed)
        await poll_msg.add_reaction("✅")
        await poll_msg.add_reaction("❌")

        polls[poll_msg.id] = {
            "yes": 0,
            "no": 0,
            "voters": set(),
            "original": message,
            "start_time": asyncio.get_event_loop().time(),
        }

@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id not in polls or payload.user_id == bot.user.id:
        return

    poll = polls[payload.message_id]
    if payload.user_id in poll["voters"]:
        return

    if str(payload.emoji.name) == "✅":
        poll["yes"] += 1
    elif str(payload.emoji.name) == "❌":
        poll["no"] += 1
    else:
        return

    poll["voters"].add(payload.user_id)

    # Check if all staff have voted (very basic logic — can be expanded)
    staff_role = bot.get_guild(payload.guild_id).get_role(config["staff_role"])
    if staff_role:
        if all(member.id in poll["voters"] for member in staff_role.members if not member.bot):
            await conclude_poll(payload.message_id)

@tasks.loop(seconds=60)
async def check_poll_timeouts():
    now = asyncio.get_event_loop().time()
    expired = [mid for mid, p in polls.items() if now - p["start_time"] >= 86400]
    for mid in expired:
        await conclude_poll(mid)

async def conclude_poll(message_id):
    poll = polls.pop(message_id)
    result = "APPROVED ✅" if poll["yes"] > poll["no"] else "DENIED ❌"

    embed = discord.Embed(
        title="Suggestion Review Complete",
        description=f"{poll['original'].embeds[0].description}\n\nResult: **{result}**",
        color=discord.Color.green() if result == "APPROVED ✅" else discord.Color.red()
    )

    announcement_channel = bot.get_channel(config["announcement_channel"])
    announcement_role_id = config["announcement_role"]
    mention = f"<@&{announcement_role_id}>" if announcement_role_id else ""

    await announcement_channel.send(content=mention, embed=embed)

check_poll_timeouts.start()
bot.run(TOKEN)