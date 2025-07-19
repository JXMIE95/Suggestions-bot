import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# In-memory config
config = {
    "suggestion_channel": None,
    "main_channel": None,
    "staff_channel": None,
    "announcement_channel": None,
    "staff_role": None,
    "main_role": None,
    "announcement_role": None
}

SUGGESTIONS = {}
LIKE_THRESHOLD = 10
POLL_DURATION = 60 * 60 * 24  # 24 hours

class SuggestionModal(discord.ui.Modal, title="Create a Suggestion"):
    title_input = discord.ui.TextInput(label="Title", placeholder="Suggestion Title", max_length=100)
    description_input = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, max_length=1000)

    async def on_submit(self, interaction: discord.Interaction):
        main_channel_id = config.get("main_channel")
        main_role_id = config.get("main_role")

        if not main_channel_id:
            await interaction.response.send_message("Main channel not set.", ephemeral=True)
            return

        main_channel = bot.get_channel(main_channel_id)
        if not main_channel:
            await interaction.response.send_message("Main channel not found.", ephemeral=True)
            return

        embed = discord.Embed(
            title=self.title_input.value,
            description=self.description_input.value,
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar)

        mention = f"<@&{main_role_id}>" if main_role_id else "@everyone"
        message = await main_channel.send(content=f"{mention} New Suggestion!", embed=embed)
        await message.add_reaction("👍")

        SUGGESTIONS[message.id] = {
            "user_id": interaction.user.id,
            "upvotes": 0,
            "title": self.title_input.value,
            "description": self.description_input.value,
            "created": datetime.utcnow()
        }

        await interaction.response.send_message("✅ Suggestion sent to main channel!", ephemeral=True)

@tree.command(name="setup", description="Set the channels and optional roles for the bot")
@app_commands.describe(
    suggestion_channel="Channel where the suggestion buttons are posted",
    main_channel="Channel where user suggestions are posted",
    staff_channel="Channel where staff vote on approved suggestions",
    announcement_channel="Channel where final results are posted",
    staff_role="Role to notify for staff polls (optional)",
    main_role="Role to notify for user suggestions (optional)",
    announcement_role="Role to notify in the announcement channel (optional)"
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

    await interaction.response.send_message("✅ Setup completed!", ephemeral=True)

class SuggestionButtons(discord.ui.View):
    @discord.ui.button(label="Make a Suggestion", style=discord.ButtonStyle.primary)
    async def make_suggestion(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SuggestionModal())

    @discord.ui.button(label="View My Suggestions", style=discord.ButtonStyle.secondary)
    async def view_suggestions(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔍 Viewing suggestions is coming soon!", ephemeral=True)

@tree.command(name="post_buttons", description="Post the Suggestion buttons")
async def post_buttons(interaction: discord.Interaction):
    await interaction.response.send_message("📝 Suggestion Panel", view=SuggestionButtons())

@bot.event
async def on_raw_reaction_add(payload):
    if payload.emoji.name != "👍":
        return

    if payload.message_id not in SUGGESTIONS:
        return

    suggestion = SUGGESTIONS[payload.message_id]
    suggestion["upvotes"] += 1

    if suggestion["upvotes"] == LIKE_THRESHOLD:
        guild = bot.get_guild(payload.guild_id)
        staff_channel = bot.get_channel(config["staff_channel"])
        staff_role = guild.get_role(config["staff_role"]) if config["staff_role"] else None

        embed = discord.Embed(
            title=f"Staff Review: {suggestion['title']}",
            description=suggestion["description"],
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Vote within 24 hours (👍 = Yes, 👎 = No)")

        mention = staff_role.mention if staff_role else ""
        poll_msg = await staff_channel.send(content=mention, embed=embed)
        await poll_msg.add_reaction("👍")
        await poll_msg.add_reaction("👎")

        asyncio.create_task(handle_poll_result(poll_msg, suggestion))

async def handle_poll_result(message, suggestion):
    await asyncio.sleep(POLL_DURATION)

    message = await message.channel.fetch_message(message.id)
    yes_votes = 0
    no_votes = 0

    for reaction in message.reactions:
        if str(reaction.emoji) == "👍":
            yes_votes = reaction.count - 1
        elif str(reaction.emoji) == "👎":
            no_votes = reaction.count - 1

    result = "✅ Approved" if yes_votes > no_votes else "❌ Rejected"

    announcement_channel = bot.get_channel(config["announcement_channel"])
    role_mention = f"<@&{config['announcement_role']}>" if config["announcement_role"] else ""

    embed = discord.Embed(
        title=f"Suggestion Result: {suggestion['title']}",
        description=f"**{result}**\n👍 {yes_votes} | 👎 {no_votes}",
        color=discord.Color.gold()
    )

    await announcement_channel.send(content=role_mention, embed=embed)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")

bot.run(TOKEN)