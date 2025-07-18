import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import asyncio
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# In-memory config (replace with database if needed)
config = {
    "suggestion_channel": None,
    "main_channel": None,
    "staff_channel": None,
    "announcement_channel": None,
    "staff_role": None,
    "announcement_role": None
}

SUGGESTIONS = {}
LIKE_THRESHOLD = 10
POLL_DURATION = 60 * 60 * 24  # 24 hours in seconds

class SuggestionModal(discord.ui.Modal, title="Create a Suggestion"):
    title_input = discord.ui.TextInput(label="Title", placeholder="Suggestion Title", max_length=100)
    description_input = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, max_length=1000)

    async def on_submit(self, interaction: discord.Interaction):
        main_channel_id = config.get("main_channel")
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

        message = await main_channel.send(content="@everyone New Suggestion!", embed=embed)
        await message.add_reaction("👍")

        SUGGESTIONS[message.id] = {
            "user_id": interaction.user.id,
            "upvotes": 0,
            "title": self.title_input.value,
            "description": self.description_input.value,
            "created": datetime.utcnow()
        }

        await interaction.response.send_message("✅ Suggestion sent to main channel!", ephemeral=True)

@tree.command(name="setup_channels", description="Set the required channel and role IDs")
@app_commands.describe(
    suggestion_channel="Channel for suggestion buttons",
    main_channel="Channel where suggestions are posted",
    staff_channel="Channel for staff to vote on suggestions",
    announcement_channel="Channel to post results",
    staff_role="Role to mention in staff polls",
    announcement_role="Role to mention in announcement"
)
async def setup_channels(
    interaction: discord.Interaction,
    suggestion_channel: discord.TextChannel,
    main_channel: discord.TextChannel,
    staff_channel: discord.TextChannel,
    announcement_channel: discord.TextChannel,
    staff_role: discord.Role,
    announcement_role: discord.Role
):
    config["suggestion_channel"] = suggestion_channel.id
    config["main_channel"] = main_channel.id
    config["staff_channel"] = staff_channel.id
    config["announcement_channel"] = announcement_channel.id
    config["staff_role"] = staff_role.id
    config["announcement_role"] = announcement_role.id

    await interaction.response.send_message("✅ Channels and roles configured!", ephemeral=True)

class SuggestionButtons(discord.ui.View):
    @discord.ui.button(label="Make a Suggestion", style=discord.ButtonStyle.primary)
    async def suggest(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SuggestionModal())

    @discord.ui.button(label="View My Suggestions", style=discord.ButtonStyle.secondary)
    async def view_suggestions(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Placeholder: You can implement this to fetch user's suggestions from storage
        await interaction.response.send_message("🔍 This feature is under development.", ephemeral=True)

@tree.command(name="post_buttons", description="Post the Suggestion buttons")
async def post_buttons(interaction: discord.Interaction):
    await interaction.response.send_message("📝 Suggestion panel", view=SuggestionButtons())

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
        staff_role = guild.get_role(config["staff_role"])

        embed = discord.Embed(
            title=f"Staff Review: {suggestion['title']}",
            description=suggestion["description"],
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Vote within 24 hours (👍 = Yes, 👎 = No)")

        poll_message = await staff_channel.send(content=f"{staff_role.mention} Please vote:", embed=embed)
        await poll_message.add_reaction("👍")
        await poll_message.add_reaction("👎")

        asyncio.create_task(collect_poll_results(poll_message, suggestion))

async def collect_poll_results(message, suggestion):
    await asyncio.sleep(POLL_DURATION)

    message = await message.channel.fetch_message(message.id)
    votes = {"yes": 0, "no": 0}
    for reaction in message.reactions:
        if str(reaction.emoji) == "👍":
            votes["yes"] = reaction.count - 1
        elif str(reaction.emoji) == "👎":
            votes["no"] = reaction.count - 1

    result = "✅ Approved!" if votes["yes"] > votes["no"] else "❌ Rejected!"
    announce_channel = bot.get_channel(config["announcement_channel"])
    mention_role = bot.get_guild(message.guild.id).get_role(config["announcement_role"])

    embed = discord.Embed(
        title=f"Suggestion Result: {suggestion['title']}",
        description=f"**{result}**\n👍 {votes['yes']} | 👎 {votes['no']}",
        color=discord.Color.gold()
    )

    await announce_channel.send(content=f"{mention_role.mention}", embed=embed)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")

bot.run(TOKEN)