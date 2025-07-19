import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timedelta

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# In-memory storage
config = {
    "suggestions_channel": None,
    "main_channel": None,
    "staff_channel": None,
    "announcement_channel": None,
    "staff_role": None,
    "main_role": None,
    "announcement_role": None,
}

suggestions = {}  # message_id: {"author_id": x, "upvotes": 0, "poll_started": False}
polls = {}        # staff_msg_id: {"yes": 0, "no": 0, "votes": set(), "deadline": datetime, "original_msg": discord.Message}

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print("❌ Failed to sync commands:", e)

    if not check_poll_timeouts.is_running():
        check_poll_timeouts.start()

@tree.command(name="setup", description="Configure bot channels and roles")
@app_commands.describe(
    suggestions_channel="Channel for suggestions",
    main_channel="Main chat channel",
    staff_channel="Staff review channel",
    announcement_channel="Final announcement channel",
    staff_role="Staff role to mention in polls",
    main_role="Main role to mention for suggestions",
    announcement_role="Role to mention in announcements"
)
async def setup(
    interaction: discord.Interaction,
    suggestions_channel: discord.TextChannel,
    main_channel: discord.TextChannel,
    staff_channel: discord.TextChannel,
    announcement_channel: discord.TextChannel,
    staff_role: discord.Role = None,
    main_role: discord.Role = None,
    announcement_role: discord.Role = None
):
    config["suggestions_channel"] = suggestions_channel.id
    config["main_channel"] = main_channel.id
    config["staff_channel"] = staff_channel.id
    config["announcement_channel"] = announcement_channel.id
    config["staff_role"] = staff_role.id if staff_role else None
    config["main_role"] = main_role.id if main_role else None
    config["announcement_role"] = announcement_role.id if announcement_role else None

    view = discord.ui.View()
    view.add_item(MakeSuggestion())
    view.add_item(ViewSuggestions())
    await suggestions_channel.send("📢 Use the buttons below to interact with the suggestion system:", view=view)

    await interaction.response.send_message("✅ Channels and roles configured!", ephemeral=True)

class MakeSuggestion(discord.ui.Button):
    def __init__(self):
        super().__init__(label="📨 Make a Suggestion", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        modal = SuggestionModal()
        await interaction.response.send_modal(modal)

class ViewSuggestions(discord.ui.Button):
    def __init__(self):
        super().__init__(label="📂 View My Suggestions", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        user_suggestions = [
            f"- {sugg['content']}" for sugg in suggestions.values() if sugg['author_id'] == interaction.user.id
        ]
        content = "\n".join(user_suggestions) if user_suggestions else "You haven't made any suggestions yet."
        await interaction.response.send_message(content, ephemeral=True)

class SuggestionModal(discord.ui.Modal, title="Submit Suggestion"):
    title_input = discord.ui.TextInput(label="Title", max_length=100)
    desc_input = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, max_length=400)

    async def on_submit(self, interaction: discord.Interaction):
        main_channel = bot.get_channel(config["main_channel"])
        role_mention = f"<@&{config['main_role']}>" if config["main_role"] else ""

        embed = discord.Embed(title=self.title_input.value, description=self.desc_input.value, color=0x00ff00)
        embed.set_footer(text=f"Suggested by {interaction.user}")

        msg = await main_channel.send(content=role_mention, embed=embed)
        await msg.add_reaction("👍")

        suggestions[msg.id] = {
            "author_id": interaction.user.id,
            "upvotes": 0,
            "poll_started": False,
            "content": f"{self.title_input.value}: {self.desc_input.value}"
        }

        await interaction.response.send_message("✅ Suggestion submitted!", ephemeral=True)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    if reaction.message.id not in suggestions:
        return

    if str(reaction.emoji) == "👍":
        suggestions[reaction.message.id]["upvotes"] += 1
        if suggestions[reaction.message.id]["upvotes"] >= 1 and not suggestions[reaction.message.id]["poll_started"]:
            await start_staff_poll(reaction.message)

async def start_staff_poll(message):
    suggestions[message.id]["poll_started"] = True
    staff_channel = bot.get_channel(config["staff_channel"])
    staff_role = f"<@&{config['staff_role']}>" if config["staff_role"] else ""

    embed = discord.Embed(
        title="📊 Staff Poll",
        description=message.embeds[0].description,
        color=0xffc107
    )
    embed.set_footer(text="React with ✅ or ❌ to vote. 24-hour timer.")

    poll_msg = await staff_channel.send(content=staff_role, embed=embed)
    await poll_msg.add_reaction("✅")
    await poll_msg.add_reaction("❌")

    polls[poll_msg.id] = {
        "yes": 0,
        "no": 0,
        "votes": set(),
        "deadline": datetime.utcnow() + timedelta(hours=24),
        "original_msg": poll_msg,
        "original_embed": message.embeds[0]
    }

@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id not in polls or payload.user_id == bot.user.id:
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if not member:
        return

    poll = polls[payload.message_id]
    if payload.user_id in poll["votes"]:
        return  # already voted

    if str(payload.emoji.name) == "✅":
        poll["yes"] += 1
    elif str(payload.emoji.name) == "❌":
        poll["no"] += 1
    else:
        return

    poll["votes"].add(payload.user_id)

    staff_role = guild.get_role(config["staff_role"])
    if staff_role and all(member.id in poll["votes"] for member in staff_role.members if not member.bot):
        await send_poll_result(payload.message_id, guild)

@tasks.loop(minutes=1)
async def check_poll_timeouts():
    now = datetime.utcnow()
    to_remove = []
    for poll_id, data in polls.items():
        if now >= data["deadline"]:
            guild = bot.get_guild(data["original_msg"].guild.id)
            await send_poll_result(poll_id, guild)
            to_remove.append(poll_id)
    for poll_id in to_remove:
        del polls[poll_id]

async def send_poll_result(poll_id, guild):
    poll = polls[poll_id]
    announcement_channel = guild.get_channel(config["announcement_channel"])
    announcement_role = f"<@&{config['announcement_role']}>" if config["announcement_role"] else ""

    result_text = "✅ Approved!" if poll["yes"] > poll["no"] else "❌ Rejected!"
    embed = discord.Embed(
        title="📢 Poll Result",
        description=f"{poll['original_embed'].description}\n\n**Result:** {result_text}",
        color=0x3498db if poll["yes"] > poll["no"] else 0xe74c3c
    )
    await announcement_channel.send(content=announcement_role, embed=embed)

bot.run(TOKEN)