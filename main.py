import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timedelta

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Global settings
CONFIG = {
    "suggestion_channel": None,
    "main_channel": None,
    "staff_channel": None,
    "announcement_channel": None,
    "main_role": None,
    "staff_role": None,
    "announcement_role": None,
}

polls = {}

class SuggestionModal(discord.ui.Modal, title="Submit a Suggestion"):
    title_input = discord.ui.TextInput(label="Suggestion Title", required=True, max_length=100)
    description_input = discord.ui.TextInput(label="Suggestion Description", required=True, style=discord.TextStyle.paragraph)

    def __init__(self, user):
        super().__init__()
        self.user = user

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title=self.title_input.value, description=self.description_input.value, color=discord.Color.blurple())
        embed.set_footer(text=f"Suggested by {self.user.name}")
        embed.timestamp = datetime.utcnow()

        main_channel = bot.get_channel(CONFIG["main_channel"])
        main_role = interaction.guild.get_role(CONFIG["main_role"])

        msg = await main_channel.send(content=main_role.mention if main_role else "", embed=embed)
        await msg.add_reaction("👍")

        polls[msg.id] = {
            "original_embed": embed,
            "thumbs_up": 0,
            "suggestion_msg": msg,
            "votes": {},
            "start_time": datetime.utcnow(),
            "resolved": False
        }

        await interaction.response.send_message("Your suggestion has been submitted!", ephemeral=True)

class SuggestionButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Make a Suggestion", style=discord.ButtonStyle.green, custom_id="make_suggestion")
    async def make_suggestion(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SuggestionModal(user=interaction.user))

@tree.command(name="setup", description="Configure bot channels and roles.")
@app_commands.describe(
    suggestion_channel="Channel where suggestion buttons appear",
    main_channel="Channel where suggestions are posted",
    staff_channel="Channel where staff votes",
    announcement_channel="Channel where results go",
    main_role="Role to ping on suggestions",
    staff_role="Role to vote on suggestions",
    announcement_role="Role to ping in announcements"
)
async def setup(interaction: discord.Interaction,
    suggestion_channel: discord.TextChannel,
    main_channel: discord.TextChannel,
    staff_channel: discord.TextChannel,
    announcement_channel: discord.TextChannel,
    main_role: discord.Role = None,
    staff_role: discord.Role = None,
    announcement_role: discord.Role = None
):
    CONFIG.update({
        "suggestion_channel": suggestion_channel.id,
        "main_channel": main_channel.id,
        "staff_channel": staff_channel.id,
        "announcement_channel": announcement_channel.id,
        "main_role": main_role.id if main_role else None,
        "staff_role": staff_role.id if staff_role else None,
        "announcement_role": announcement_role.id if announcement_role else None,
    })

    await suggestion_channel.send("Use the button below to submit suggestions:", view=SuggestionButtons())
    await interaction.response.send_message("✅ Setup complete.", ephemeral=True)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    msg_id = payload.message_id
    emoji = str(payload.emoji)

    if msg_id in polls and emoji == "👍":
        polls[msg_id]["thumbs_up"] += 1

        if polls[msg_id]["thumbs_up"] >= 10 and not polls[msg_id]["resolved"]:
            await send_to_staff_poll(msg_id)

async def send_to_staff_poll(msg_id):
    poll = polls[msg_id]
    poll["resolved"] = True

    staff_channel = bot.get_channel(CONFIG["staff_channel"])
    staff_role = staff_channel.guild.get_role(CONFIG["staff_role"])

    embed = discord.Embed(
        title=f"📊 Diplomat Poll: {poll['original_embed'].title}",
        description=f"{poll['original_embed'].description}",
        color=discord.Color.orange()
    )
    embed.set_footer(text="React with ✅ or ❌ — 24h timer")

    msg = await staff_channel.send(content=staff_role.mention if staff_role else "", embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    poll["staff_msg"] = msg
    poll["votes"] = {}
    poll["start_time"] = datetime.utcnow()

@tasks.loop(seconds=60)
async def check_poll_timeouts():
    for poll in list(polls.values()):
        if "staff_msg" not in poll or poll.get("finished"):
            continue

        msg = poll["staff_msg"]
        staff_role = msg.guild.get_role(CONFIG["staff_role"])
        announcement_channel = bot.get_channel(CONFIG["announcement_channel"])
        announcement_role = msg.guild.get_role(CONFIG["announcement_role"])

        msg = await msg.channel.fetch_message(msg.id)
        yes_votes = [user async for user in msg.reactions[0].users() if not user.bot]
        no_votes = [user async for user in msg.reactions[1].users() if not user.bot]

        all_voted = False
        if staff_role:
            total_staff = [m for m in staff_role.members if not m.bot]
            all_voted = all(m in yes_votes + no_votes for m in total_staff)

        timed_out = datetime.utcnow() - poll["start_time"] > timedelta(hours=24)

        if all_voted or timed_out:
            passed = len(yes_votes) > len(no_votes)
            embed = discord.Embed(
                title="✅ Suggestion Passed by Diplomats" if passed else "❌ Suggestion Rejected by Diplomats",
                description=poll["original_embed"].description,
                color=discord.Color.green() if passed else discord.Color.red()
            )
            await announcement_channel.send(content=announcement_role.mention if announcement_role else "", embed=embed)
            poll["finished"] = True

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    check_poll_timeouts.start()

bot.run(TOKEN)